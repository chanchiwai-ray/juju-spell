"""Basic logic of showing controller information.

Provides different ways to run the Juju command:

    - Batch: 20 commands in 5 parallel
    - Parallel: 20 in parallel
    - Serial: 20 commands in 1 parallel
"""
import logging
from argparse import Namespace
from typing import Any, Dict, List

from juju_spell.commands.base import BaseJujuCommand
from juju_spell.config import Controller
from juju_spell.connections import connect_manager, get_controller

logger = logging.getLogger(__name__)

RESULT_TYPE = Dict[str, Dict[str, Any]]
RESULTS_TYPE = List[RESULT_TYPE]


def get_result(controller_config: Controller, output: Any) -> RESULT_TYPE:
    """Get command result."""
    return {
        "context": {
            "name": controller_config.name,
            "customer": controller_config.customer,
        },
        "output": output,
    }


async def run_parallel(command: BaseJujuCommand, parsed_args: Namespace):
    pass


async def run_serial(command: BaseJujuCommand, parsed_args: Namespace) -> RESULTS_TYPE:
    """Run controller target command serially.

    Parameters:
        command(BaseJujuCommand): command to run
        parsed_args(Namespace): Namespace from CLI
    Returns:
        results(Dict): Controller dict with result.
    """
    results: RESULTS_TYPE = []
    for controller_config in parsed_args.filter.controllers:
        controller = await get_controller(controller_config)
        logger.debug("%s running in serial", controller.controller_uuid)
        command_kwargs = vars(parsed_args)
        output = await command.run(controller=controller, **command_kwargs)
        results.append(get_result(controller_config, output))

    return results


async def run_batch(command: BaseJujuCommand, parsed_args: Namespace):
    pass


async def run(command: BaseJujuCommand, parsed_args: Namespace):
    try:
        run_type = parsed_args.run_type
        logger.info("running with run_type: %s", run_type)
        if run_type == "parallel":
            return await run_parallel(command, parsed_args)
        if run_type == "batch":
            return await run_batch(command, parsed_args)

        return await run_serial(command, parsed_args)
    finally:
        await connect_manager.clean()