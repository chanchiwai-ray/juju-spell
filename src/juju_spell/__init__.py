"""Juju Spell package."""

from dataclasses import dataclass
from uuid import uuid4

from rich.console import Console
from typer import Context, Exit, Option, Typer
from typing_extensions import Annotated

from juju_spell.react_agent import get_juju_react_agent
from juju_spell.tools import tools

app = Typer(
    help="Run Juju commands with LLM.",
    context_settings={"help_option_names": ["-h", "--help"]},
)

console = Console()


@dataclass
class CommonOptions:
    """Common Options shared by all subcommands."""

    verbose: bool = False


@app.command()
def run(
    ctx: Context,
    query: str,
    model: Annotated[str, Option(help="The LLM model to use.")] = "llama3.1",
) -> None:
    """Ask LLM a question and run operations on behalf of you."""
    if not query:
        console.print("Argument 'query' cannot be empty.")
        raise Exit(code=1)

    agent = get_juju_react_agent(model, tools, console)
    if ctx.obj.verbose:
        agent.list_available_tools()
    agent.run(query, {"configurable": {"thread_id": uuid4()}})


@app.command()
def chat(
    ctx: Context,
    model: Annotated[str, Option(help="The LLM model to use.")] = "llama3.1",
) -> None:
    """Ask LLM questions interactively and run operations on behalf of you."""
    agent = get_juju_react_agent(model, tools, console)
    agent.draw_graph()
    if ctx.obj.verbose:
        agent.list_available_tools()
    agent.chat({"configurable": {"thread_id": uuid4()}})


@app.callback()
def entrypoint(
    ctx: Context,
    verbose: Annotated[bool, Option("-v", "--verbose", help="Be verbose.")] = False,
) -> None:
    """Entrypoint of the root CLI."""
    ctx.obj = CommonOptions(verbose=verbose)
