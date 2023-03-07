"""Command to show controllers information."""
import json
from typing import Any

from juju_spell.commands.base import JujuReadWriteCommand
from juju_spell.connections import get_controller


class GetController(JujuReadWriteCommand):
    """Command to get a controller."""

    async def execute(
        self, command_arguments, prev_results=None, pre_process_inputs=None, **kwargs: Any
    ) -> Any:
        """Execute main code.

        Changed name because this has to override base_command.
        """
        controller = await get_controller(command_arguments["controller_config"])
        self.logger.debug("%s get: %s", controller.controller_uuid, controller.controller_name)
        return controller

    def load_from_cache(self, file):
        if not file.exists():
            self.logger.debug("failed to read cache: no cache found.")
            return {}

        content = {}
        with open(file, "r", encoding="UTF-8") as fp:
            try:
                content = json.load(fp)
                self.logger.debug("loaded cache for %s: %s.", self.name, json.dumps(content))
            except Exception as error:
                self.logger.debug("failed to read cache: %s.", str(error))
        return content

    def save_to_cache(self, file, result):
        with open(file, "w", encoding="UTF-8") as fp:
            try:
                success = result.success
                controller = result.output
                error = result.error
                if not success:
                    raise ValueError(
                        f"failed to create cache because {self.name} run failed: {str(error)}."
                    )
                content = {
                    "uuid": controller.controller_uuid,
                    "name": controller.controller_name,
                }
                json.dump(content, fp)
                self.logger.debug("created cache for %s: %s.", self.name, json.dumps(content))
            except Exception as error:
                self.logger.debug("failed to create cache: %s.", str(error))
