"""Juju ReAct agent using ollama."""

import json
from typing import Any, Literal, cast

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langgraph.graph.state import StateGraph
from langgraph.types import Command, interrupt
from prompt_toolkit import prompt
from rich.console import Console
from rich.table import Table


class JujuReActAgent:
    """The ReAct Agent for Juju."""

    def __init__(
        self,
        model: ChatOllama,
        tools: list[BaseTool],
        console: Console,
        system_prompt: str = (
            "You are a helpful assistant who answers questions accurately using the "
            "available tools."
        ),
    ):
        """Initialize the Juju ReAct agent."""
        self._tools = tools
        self._system_prompt = system_prompt
        self._console = console
        self._model = model.bind_tools(tools)
        self._builder = StateGraph(state_schema=MessagesState)

        self._builder.add_node("get_plan", self._get_plan)
        self._builder.add_node("human_review", self._human_review)
        self._builder.add_node("execute_plan", self._execute_plan)

        self._builder.add_edge("__start__", "get_plan")
        self._builder.add_conditional_edges("get_plan", self._end_or_human_review)
        self._builder.add_edge("execute_plan", "get_plan")
        self._compiled_graph = self._builder.compile(checkpointer=MemorySaver())

    def _get_plan(self, state: MessagesState) -> MessagesState:
        """Run LLM to get action plan."""
        query = state["messages"]
        prompt = (SystemMessage(self._system_prompt) + query).format_messages()
        response = cast(AIMessage, self._model.invoke(prompt))
        return {"messages": [response]}

    def _end_or_human_review(self, state: MessagesState) -> Literal["__end__", "human_review"]:
        get_plan_message = cast(AIMessage, state["messages"][-1])
        if not get_plan_message.tool_calls:
            return "__end__"
        return "human_review"

    def _human_review(self, _: MessagesState) -> Command[Literal["__end__", "execute_plan"]]:
        """Interrupt and wait for human review."""
        if not interrupt({"question": "Can I continue with the action plan (y/yes/n/no)? "}):
            return Command(goto="__end__")
        return Command(goto="execute_plan")

    def _execute_plan(self, state: MessagesState) -> dict[str, list[Any]]:
        """Execute the action plan."""
        results = []
        get_plan_message = cast(AIMessage, state["messages"][-1])
        available_tools = {tool.name: tool for tool in self._tools}
        for t in get_plan_message.tool_calls:
            result = available_tools[t["name"]].invoke(t["args"])
            content = result if isinstance(result, str) else json.dumps(result, indent=2)
            results.append(ToolMessage(content=content, name=t["name"], tool_call_id=t["id"]))
        return {"messages": results}

    def _handle_get_plan(self, message: AIMessage) -> bool:
        """Handle get plan node."""
        if message.tool_calls:
            available_tools = {tool.name: tool for tool in self._tools}
            table = Table(title="Action Plan", title_style="")
            table.add_column("Name")
            table.add_column("Arguments")
            table.add_column("Availability")
            end = False
            for t in message.tool_calls:
                tool_exist = t["name"] in available_tools
                if not tool_exist:
                    end = True
                table.add_row(t["name"], json.dumps(t["args"]), str(tool_exist))
            self._console.print(" Ai Message ".center(80, "="))
            self._console.print("\nI want to perform the following actions:\n")
            self._console.print(table)
            if end:
                self._console.print("\nHowever, I don't have enough tools...\n")
                return False
        else:
            self._console.print(message.pretty_repr())
        self._console.print()
        return True

    def _handle_human_review(self, interrupts: tuple[Any]) -> bool:
        """Handle human review interrupt."""
        if interrupts:
            answer = prompt(f"{interrupts[0].value['question']} \n> ").lower()
            self._console.print()
            if answer not in {"y", "yes"}:
                return False
        return True

    def _handle_execute_plan(self, tool_messages: list[ToolMessage]) -> None:
        """Handle execute plan node."""
        for tool_message in tool_messages:
            self._console.print(" Tool Message ".center(80, "="))
            self._console.print(f"\nName: {tool_message.name}\n")
            self._console.print(tool_message.content)

    def run(self, query: str, config: RunnableConfig) -> None:
        """Ask the agent to create an action plan and run the plan when user approved."""
        initial_state = {"messages": [HumanMessage(query)]}
        try:
            events = self._compiled_graph.stream(initial_state, config, stream_mode="updates")
            while event := next(events):
                if get_plan := event.get("get_plan"):
                    if not self._handle_get_plan(get_plan["messages"][0]):
                        return
                elif interrupts := event.get("__interrupt__"):
                    if not self._handle_human_review(interrupts):
                        return
                    cmd: Command = Command(resume=True)
                    events = self._compiled_graph.stream(cmd, config, stream_mode="updates")
                elif execute_plan := event.get("execute_plan"):
                    self._handle_execute_plan(execute_plan["messages"])
        except StopIteration:
            return

    def chat(self, config: RunnableConfig) -> None:
        """Start an interactive chat loop with the agent, and create action plans."""
        self._console.print("\nType 'q' or 'quit' to quit.")
        while True:
            try:
                query = prompt("\nQuery: ").strip().lower()
                if query in {"q", "quit"}:
                    break
                self.run(query, config)
            except Exception as e:
                self._console.print(f"\nError: {str(e)}")

    def list_available_tools(self) -> None:
        """List available tools to stdout."""
        table = Table(title="Available Tools", title_style="")
        table.add_column("Name")
        table.add_column("Description")
        for tool in self._tools:
            table.add_row(tool.name, tool.description)
        self._console.print(table)
        self._console.print()

    def draw_graph(self) -> None:
        """Draw the graph to stdout."""
        self._console.print(self._compiled_graph.get_graph().draw_ascii())


def get_juju_react_agent(model: str, tools: list[BaseTool], console: Console) -> JujuReActAgent:
    """Get an instance of juju ReAct agent."""
    ollama = ChatOllama(model=model, temperature=0.8, num_predict=1024)
    return JujuReActAgent(ollama, tools, console)
