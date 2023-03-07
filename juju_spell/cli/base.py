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

"""JujuSpell base cli command."""
import argparse
from abc import ABCMeta
from typing import Optional, Type

from craft_cli import BaseCommand, emit
from craft_cli.dispatcher import _CustomArgumentParser

from juju_spell.assignment.runner import get_runner
from juju_spell.cli.utils import parse_comma_separated_str, parse_filter
from juju_spell.commands.base import Command
from juju_spell.config import Config


class BaseJujuCMD(BaseCommand, metaclass=ABCMeta):
    """Base CLI command for handling any Juju commands."""

    command: Type[Command]

    def __init__(self, config: Config) -> None:
        """Initialize BaseCMD."""
        super().__init__(config=None)
        # overwrite config in BaseCommand
        self.config: Config = config  # type: ignore

    def run(self, parsed_args: argparse.Namespace) -> Optional[int]:
        """Execute CLI command.

        **This function should not be changed.**
        """
        runner = get_runner(parsed_args.run_type)
        results = runner(self.config, self.command, parsed_args).run()
        emit.message("\n".join([str(result[-1]) for result in results])) # FIXME: we really need a DAG

    def fill_parser(self, parser: _CustomArgumentParser) -> None:
        """Define base arguments for Juju commands.

        This will add arguments for connection, filtering and config.
        """
        parser.add_argument(
            "--run-type",
            type=str,
            choices=["parallel", "batch", "serial"],
            default="serial",
            help="parallel, batch or serial",
        )
        parser.add_argument(
            "--filter",
            type=parse_filter,
            required=False,
            default="",
            help=(
                "Key-value pair comma separated string in double quotes e.g., "
                '"a=1,2,3 b=4,5,6". '
            ),
        )
        parser.add_argument(
            "-c",
            "--controllers",
            type=parse_comma_separated_str,
            help="controller filter",
        )
        parser.add_argument(
            "-m",
            "--models",
            type=parse_comma_separated_str,
            help="model filter",
        )


class JujuReadCMD(BaseJujuCMD, metaclass=ABCMeta):
    """Base CLI command for handling Juju commands with read access."""

    def fill_parser(self, parser):
        super().fill_parser(parser)
        parser.add_argument(
            "--refresh",
            default=False,
            action="store_true",
            help="This will force pulling latest information from the controllers.",
        )


class JujuWriteCMD(BaseJujuCMD, metaclass=ABCMeta):
    """Base CLI command for handling Juju commands with write access."""

    def fill_parser(self, parser):
        super().fill_parser(parser)
        parser.add_argument(
            "--dry-run",
            default=False,
            action="store_true",
            help=("This will only run pre-check and dry-run only instead of real execution."),
        )
        parser.add_argument(
            "--no-confirm",
            default=False,
            action="store_true",
            help="This will skip all the confirm check.",
        )
