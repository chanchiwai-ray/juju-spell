"""Basic logic of showing controller information.

Provides different ways to run the Juju command:

    - Batch: 20 commands in 5 parallel
    - Parallel: 20 in parallel
    - Serial: 20 commands in 1 parallel
"""
import asyncio
import logging
from abc import ABCMeta, abstractmethod
from dataclasses import asdict
from typing import Any, Dict, List

from juju_spell.commands.base import Result
from juju_spell.config import Controller
from juju_spell.connections import connect_manager
from juju_spell.filter import get_filtered_config

logger = logging.getLogger(__name__)

ResultType = Dict[str, Dict[str, Any]]
ResultsType = List[ResultType]


def get_result(controller_config: Controller, output: Result) -> ResultType:
    """Get command result."""
    return {
        "context": {
            "uuid": controller_config.uuid,
            "name": controller_config.name,
            "customer": controller_config.customer,
        },
        **asdict(output),
    }


def get_runner(run_type):
    logger.info("running with run_type: %s", run_type)
    if run_type == "parallel":
        return ParallelRunner
    elif run_type == "batch":
        return SequentialRunner
    else:
        return SequentialRunner


class Runner(metaclass=ABCMeta):
    def __init__(self, config, command, parsed_args):
        """FIXME."""
        self.config = config
        self.command = command
        self.parsed_args = parsed_args
        self._tasks = []
        self.build_tasks()

    def build_tasks(self):
        filtered_config = get_filtered_config(self.config, self.parsed_args.filter)
        for controller_config in filtered_config.controllers:
            self._tasks.append(task(controller_config, self.command, self.parsed_args))

    @abstractmethod
    def run(self) -> Any:
        pass


async def task(controller_config, command, parsed_args):
    try:
        command_arguments = vars(parsed_args)
        command_arguments["controller_config"] = controller_config
        return await command(command_arguments)
    finally:
        pass  # this will break parallel execution
        # await connect_manager.clean()


class ParallelRunner(Runner):
    def __init__(self, config, command, parsed_args):
        """FIXME."""
        super().__init__(config, command, parsed_args)

    def run(self) -> Any:
        """Execute Juju Commands."""
        loop = asyncio.get_event_loop()
        tasks = []
        # broken, because of connect_manager.clean() closes all connections
        for task in self._tasks:
            tasks.append(loop.create_task(task))
        loop.run_until_complete(asyncio.gather(*tasks))
        return [task.result() for task in tasks]


class BatchRunner(Runner):
    def __init__(self, config, command, parsed_args):
        """FIXME."""
        super().__init__(config, command, parsed_args)

    def run(self) -> Any:
        raise NotImplementedError("running in batches is not yet supported")


class SequentialRunner(Runner):
    def __init__(self, config, command, parsed_args):
        """FIXME."""
        super().__init__(config, command, parsed_args)

    def run(self) -> Any:
        """Execute Juju Commands."""
        loop = asyncio.get_event_loop()
        results = []
        for task in self._tasks:
            task = loop.create_task(task)
            loop.run_until_complete(asyncio.gather(task))
            results.append(task.result())
        return results
