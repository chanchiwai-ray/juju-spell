"""Command to check connection to controllers."""
import json
from typing import Any

from juju import juju

from juju_spell.commands.base import JujuReadCommand


class ListModels(JujuReadCommand):
    """FIXME."""

    def pre_process(self, command_arguments, prev_results=None, **kwargs):
        if prev_results is None:
            raise ValueError(
                f"failed to run {self.name}: expecting `prev_results` from GetController."
            )
        if prev_results and len(prev_results) > 0 and not prev_results[-1].success:
            raise prev_results[-1].error

        prev_result = prev_results[-1]
        if not isinstance(prev_result.output, juju.Controller):
            raise ValueError(
                f"failed to run {self.name}: expecting `prev_results[-1].output` is of type juju.Controller."
            )

    async def execute(
        self, command_arguments, prev_results=None, pre_process_inputs=None, **kwargs: Any
    ) -> Any:
        """FIXME."""

        controller = prev_results[-1].output
        outputs = {"models": list(await controller.list_models())}
        self.logger.debug("%s list models: %s", controller.controller_uuid, outputs["models"])
        return outputs["models"]

    def load_from_cache(self, file):
        if not file.exists():
            self.logger.debug("failed to read cache: no cache found.")
            return {}

        content = {}
        with open(file, "r", encoding="UTF-8") as fp:
            try:
                content = json.load(fp)
                if "models" not in content:
                    raise ValueError("no cache for models.")
                self.logger.debug(
                    "loaded cache for %s: %s", self.name, json.dumps(content["models"])
                )
            except Exception as error:
                self.logger.debug("failed to read cache: %s.", str(error))
        return content

    def save_to_cache(self, file, result):
        content = {}

        with open(file, "r", encoding="UTF-8") as fp:
            try:
                content = json.load(fp)
            except Exception as error:
                self.logger.debug("failed to read cache: %s.", str(error))

        with open(file, "w", encoding="UTF-8") as fp:
            try:
                success = result.success
                output = result.output
                error = result.error
                if not success:
                    raise ValueError(
                        f"failed to create cache because {self.name} run failed: {str(error)}."
                    )
                content.update({"models": output})
                json.dump(content, fp)
                self.logger.debug("created cache for %s: %s.", self.name, json.dumps(content))
            except Exception as error:
                self.logger.debug("failed to create cache: %s.", str(error))
