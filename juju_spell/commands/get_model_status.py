"""Command to check connection to controllers."""
import json
from typing import Any

from juju import juju

from juju_spell.commands.base import JujuReadCommand


class GetModelStatus(JujuReadCommand):
    """FIXME."""

    def pre_process(self, command_arguments, prev_results=None, **kwargs):
        pass
        # if prev_results and not prev_results.success:
        #     raise prev_results.error
        # if prev_results is None:
        #     raise ValueError(
        #         f"failed to run {self.name}: expecting `prev_results` from ListModels."
        #     )
        # if prev_results is not None and not isinstance(prev_results.output, list):
        #     raise ValueError(
        #         f"failed to run {self.name}: expecting `prev_results.output` is of type List."
        #     )

    async def execute(
        self, command_arguments, prev_results=None, pre_process_inputs=None, **kwargs: Any
    ) -> Any:
        """FIXME."""

        # FIXME: error handling
        controller = prev_results[0].output
        model_names = prev_results[1].output

        all_status = {}
        # FIXME: filter by model name, and parallel execution like in the runner.py
        for model_name in model_names:
            model = await controller.get_model(model_name)
            status = await model.get_status()
            all_status[model_name] = status
            model.disconnect()
            self.logger.debug("%s model %s status: %s", controller.controller_uuid, model_name, status)
        return all_status
