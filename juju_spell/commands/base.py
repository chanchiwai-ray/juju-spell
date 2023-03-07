# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""JujuSpell base juju command."""
import dataclasses
import json
import logging
from abc import ABCMeta, abstractmethod
from typing import Any, Optional

from craft_cli import emit

from juju_spell.settings import DEFAULT_CACHE_DIR


@dataclasses.dataclass(frozen=True)
class Result:
    """Result from command."""

    success: bool
    output: Optional[Any] = None
    error: Optional[Exception] = None

    def __repr__(self):
        emit.debug(f"formatting `{self.__dict__}`")
        if isinstance(self.__dict__, (dict, list)):
            return json.dumps(self.__dict__, default=vars, indent=2)

        return str(self.__dict__)


class SequentialCommandGroup:
    def __init__(self, commands):
        """FIXME. we really need a DAG"""
        self._commands = commands

    async def __call__(self, command_arguments, prev_results=None, **kwargs):
        results = []
        if results is not None and isinstance(prev_results, list):
            results += prev_results
        for command in self._commands:
            results.append(await command(command_arguments, prev_results=results, **kwargs))
        return results


class ParallelCommandGroup:
    def __init__(self, commands):
        """FIXME. we really need a DAG"""
        self._commands = commands

    async def __call__(self, command_arguments, prev_results=None, **kwargs):
        results = []
        for command in self._commands:
            results.append(await command(command_arguments, prev_results=prev_results, **kwargs))
        return results


class Command(metaclass=ABCMeta):
    def __init__(self):
        """Init for command."""
        self._result = None
        self.name = getattr(self.__class__, "__name__", "unknown")
        self.logger = logging.getLogger(self.name)

    async def __call__(self, command_arguments, prev_results=None, **kwargs):
        uuid = command_arguments["controller_config"].uuid

        # TODO: add dry-run

        if self.cachable and not command_arguments.get("refresh"):
            # move these somewhere else -->
            if not DEFAULT_CACHE_DIR.exists():
                DEFAULT_CACHE_DIR.mkdir()
            # move these somewhere else <--
            cached_result = self.load_from_cache(DEFAULT_CACHE_DIR / uuid)
            if cached_result:
                self._result = Result(True, output=cached_result, error=None)
                return self.result

        try:
            pre_process_inputs = self.pre_process(
                command_arguments, prev_results=prev_results, **kwargs
            )
            result = await self.execute(
                command_arguments,
                prev_results=prev_results,
                pre_process_inputs=pre_process_inputs,
                **kwargs,
            )
            post_process_result = self.post_process(
                result,
                prev_results=prev_results,
                pre_process_inputs=pre_process_inputs,
                command_arguments=command_arguments,
                **kwargs,
            )
            self._result = Result(True, output=post_process_result, error=None)
        except Exception as error:
            self.logger.exception(error)
            self._result = Result(False, output=None, error=error)
            return self.result

        if self.cachable:
            # move these somewhere else -->
            if not DEFAULT_CACHE_DIR.exists():
                DEFAULT_CACHE_DIR.mkdir()
            # move these somewhere else <--
            self.save_to_cache(DEFAULT_CACHE_DIR / uuid, result=self.result)

        return self.result

    @property
    @abstractmethod
    def cachable(self):
        pass

    @property
    @abstractmethod
    def sshuttle(self):
        pass

    @abstractmethod
    def load_from_cache(self, file):
        """FIXME."""
        pass

    @abstractmethod
    def save_to_cache(self, file, result):
        """FIXME."""
        pass

    @property
    def result(self) -> Any:
        return self._result

    def pre_process(self, command_arguments, prev_results=None, **kwargs):
        """FIXME."""
        return None

    @abstractmethod
    async def execute(
        self, command_arguments, prev_results=None, pre_process_inputs=None, **kwargs
    ):
        """FIXME."""
        pass

    def post_process(
        self,
        result,
        prev_results=None,
        pre_process_inputs=None,
        command_arguments=None,
        **kwargs,
    ):
        """FIXME."""
        return result


class JujuReadCommand(Command):
    def __init__(self):
        """FIXME."""
        super().__init__()

    @property
    def cachable(self):
        return True

    @property
    def sshuttle(self):
        return True

    def load_from_cache(self, file):
        """FIXME."""
        self.logger.debug("load_from_cache is not implemented for %s: pass though.", self.name)

    def save_to_cache(self, file, result):
        """FIXME."""
        self.logger.debug("save_to_cache is not implemented for %s: pass though.", self.name)


class JujuWriteCommand(Command):
    def __init__(self):
        """FIXME."""
        super().__init__()

    @property
    def cachable(self):
        return False

    @property
    def sshuttle(self):
        return True

    def load_from_cache(self, file):
        raise NotImplementedError("Caching is not supported for WRITE command.")

    def save_to_cache(self, file, result):
        raise NotImplementedError("Caching is not supported for WRITE command.")


class JujuReadWriteCommand(Command):
    def __init__(self):
        """FIXME."""
        super().__init__()

    @property
    def cachable(self):
        return True

    @property
    def sshuttle(self):
        return True

    def load_from_cache(self, file):
        """FIXME."""
        self.logger.debug("load_from_cache is not implemented for %s: pass though.", self.name)

    def save_to_cache(self, file, result):
        """FIXME."""
        self.logger.debug("save_to_cache is not implemented for %s: pass though.", self.name)
