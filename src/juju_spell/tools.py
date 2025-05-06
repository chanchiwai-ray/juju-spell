"""The tools supported by Juju AI."""

import json
from collections.abc import Callable
from functools import wraps
from typing import Any

from jubilant import CLIError, Juju
from langchain_core.tools import BaseTool, tool

tools: list[BaseTool] = []


def safe_run(func: Callable) -> Callable:
    """Run Juju command gracefully."""

    @wraps(func)
    def _decorator(*args: Any, **kwargs: dict[Any, Any]) -> str:
        try:
            result = func(*args, **kwargs)
        except CLIError as e:
            return str(e)
        else:
            return result

    return _decorator


def add_tool(func: Callable) -> Callable:
    """Add the tool to the list of tools supported by Juju AI."""
    safe_func = safe_run(func)
    wrapped_func = tool(safe_func, parse_docstring=True)
    tools.append(wrapped_func)
    return wrapped_func


@add_tool
def juju_debug_log(model: str | None = None, limit: int = 0) -> str:
    """Return debug log messages from a model.

    Args:
        model: If specified, operate on this Juju model, otherwise use the current Juju model.
        limit: Limit the result to the most recent limit lines. Defaults to 0, meaning return all
            lines in the log.

    Returns:
        The debug log lines.

    """
    return Juju(model=model).debug_log(limit=limit)


@add_tool
def juju_deploy(
    charm: str,
    base: str | None = None,
    channel: str | None = None,
    model: str | None = None,
    name: str | None = None,
    num_units: int = 1,
) -> str:
    """Deploy a new application.

    Args:
        charm: The name of charm or bundle to deploy.
        base: The base on which to deploy.
        channel: Channel to use when deploying from Charmhub.
        model: If specified, operate on this model, otherwise use the current model.
        name: Optional application name within the model. Defaults to the charm name.
        num_units: Number of units to deploy for principal charms.

    Returns:
        A message that indicates the if the deployment is successful or not.

    """
    args = ["deploy", charm]
    if name:
        args.append(name)
    if model:
        args.extend(["-m", model])
    if base:
        args.extend(["--base", base])
    if channel:
        args.extend(["--channel", channel])
    if num_units != 1:
        args.extend(["--num-units", str(num_units)])
    Juju().cli(*args)
    return f"{charm} deployed."


@add_tool
def juju_models() -> str:
    """Return all the models known to the current controller.

    Returns:
        All the models known to the current controller.

    """
    args = ["models"]
    return Juju().cli(*args)


@add_tool
def juju_current_model_name() -> str:
    """Get the name of the currently connected model.

    Returns:
        The name of the currently connected model.

    """
    args = ["models", "--format", "json"]
    result = json.loads(Juju().cli(*args))
    return result["current-model"]


@add_tool
def juju_add_model(model: str, controller: str | None = None) -> str:
    """Add a workload model.

    Args:
        model: The name of the model.
        controller: If specified, create model on this controller, otherwise use the current
            controller.

    Returns:
        A message that indicates the if the model creation is successful or not.

    """
    args = ["add-model", "--no-switch", model]
    if controller:
        args.extend(["-c", controller])
    return Juju().cli(*args)


@add_tool
def juju_status(model: str | None = None) -> str:
    """Report the status of the model, its machines, applications and units.

    Args:
        model: If specified, show the status of this model, otherwise show the status of current
            model.

    Returns:
        The juju status in text format.

    """
    args = ["status"]
    if model:
        args.append(model)
    return Juju().cli(*args)


@add_tool
def juju_integrate(app_1: str, app_2: str, model: str | None = None) -> str:
    """Integrate two applications.

    Args:
        app_1: One of the applications (and endpoints) to integrate.
        app_2: The other of the applications (and endpoints) to integrate.
        model: If specified, operate on this model, otherwise operate on the current model.

    Returns:
        The juju status in text format.

    """
    args = ["integrate", app_1, app_2]
    if model:
        args.extend(["-m", model])
    Juju().cli(*args)
    return f"{app_1} and {app_2} integrated."
