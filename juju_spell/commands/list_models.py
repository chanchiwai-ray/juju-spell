"""List models from the local cache or from the controllers."""
from typing import Any, Dict, List, Union

from juju.controller import Controller

from juju_spell.cache import DEFAULT_CACHE_BACKEND, use_cache
from juju_spell.commands.base import BaseJujuCommand


class ListModelsCommand(BaseJujuCommand):
    """Command to list models from the local cache or from the controllers."""

    async def execute(self, controller: Controller, **kwargs: Any) -> Dict[str, Union[List, bool]]:
        """List models from the local cache or from the controllers."""
        cache: Any = use_cache(DEFAULT_CACHE_BACKEND)
        list_models_key = f"{self.name}_{controller.controller_uuid}"
        context = None
        models = []

        if not kwargs["refresh"]:
            context = cache.get(list_models_key)
            if context:
                context["data"]["refresh"] = kwargs["refresh"]
                models = context["data"]["models"]

        if kwargs["refresh"] or context is None or cache.check_expired(list_models_key):
            models = list(
                await self.get_filtered_model_names(
                    controller=controller,
                    models=None,
                    model_mappings=kwargs["controller_config"].model_mapping,
                )
            )
            cache.put(list_models_key, {"models": models, "refresh": kwargs["refresh"]})
            context = cache.get(list_models_key)

        self.logger.debug("%s list models: %s", controller.controller_uuid, models)
        return context
