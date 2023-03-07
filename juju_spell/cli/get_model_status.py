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

"""JujuSpell juju ping command."""
import textwrap

from juju_spell.cli.base import JujuReadCMD
from juju_spell.commands.base import SequentialCommandGroup
from juju_spell.commands.get_controller import GetController
from juju_spell.commands.list_models import ListModels
from juju_spell.commands.get_model_status import GetModelStatus


class GetModelStatusCMD(JujuReadCMD):
    """Command to get model status from the local cache or from the controllers."""

    name = "status"
    help_msg = "Return the status of models from the local cache or from the controllers."
    overview = textwrap.dedent(
        """
        FIXME
        """
    )
    command = SequentialCommandGroup([
        GetController(),
        ListModels(),
        GetModelStatus(),
    ])
