"""Command to check connection to controllers."""
from typing import Any

from juju import juju

from juju_spell.commands.base import JujuReadCommand


class ControllerConnected(JujuReadCommand):
    """Check if the controller is connected or not command."""

    async def execute(
        self, command_arguments, prev_results=None, pre_process_inputs=None, **kwargs: Any
    ) -> Any:
        """FIXME."""

        controller = prev_results[-1].output
        connected = controller.is_connected()
        self.logger.debug("%s is connected '%r'", controller.controller_uuid, connected)
        return "accessible" if connected else "unreachable"
