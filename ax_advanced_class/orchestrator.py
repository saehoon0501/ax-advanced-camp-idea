from typing import Annotated, TypedDict, Literal, NotRequired
from langgraph.graph import END, StateGraph, START
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, model_validator, create_model, ConfigDict
from langchain_core.messages import BaseMessage
import operator
import functools

from llm.bedrock_client import BedrockClient
from prompts.base_prompt import BasePrompt
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder


class OrchestratorState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    previous_node: NotRequired[str]
    next: NotRequired[str]


class Orchestrator(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    worker_agents: list[CompiledStateGraph]
    orchestrator_prompt: BasePrompt
    workflow: CompiledStateGraph = None  # Make optional for init

    @model_validator(mode="after")
    def build_workflow(self) -> "Orchestrator":
        llm = BedrockClient().get_core()
        workflow_builder = StateGraph(OrchestratorState)

        def worker_node(state: OrchestratorState, graph: CompiledStateGraph):
            result = graph.invoke({"messages": state["messages"]})
            return {
                "messages": [result["messages"][-1]],
                "previous_node": state["next"],
            }

        members: list[str] = []
        for worker in self.worker_agents:
            workflow_builder.add_node(
                worker.name, functools.partial(worker_node, graph=worker)
            )
            members.append(worker.name)
        members.append(END)

        from enum import Enum

        MemberEnum = Enum("MemberEnum", {m: m for m in members})
        Router = create_model(
            "Router",
            next=(MemberEnum, ...),
        )

        orchestrator = ChatPromptTemplate.from_messages(
            [
                ("system", self.orchestrator_prompt.prompt),
                MessagesPlaceholder(variable_name="messages"),
            ],
        ) | llm.with_structured_output(Router)

        def orchestrator_node(state: OrchestratorState) -> OrchestratorState:
            if state.get("previous_node", "START") != "START":
                return {"next": END}
            result = orchestrator.invoke({"messages": state["messages"]})
            return {"messages": state["messages"], "next": result.next.value}

        def get_next_node(state: OrchestratorState) -> str:
            return state["next"]

        workflow_builder.add_node("orchestrator", orchestrator_node)
        workflow_builder.add_conditional_edges(
            "orchestrator",
            get_next_node,
            {member: member for member in members},
        )
        workflow_builder.add_edge(START, "orchestrator")

        for member in members[:-1]:
            workflow_builder.add_edge(member, "orchestrator")

        self.workflow = workflow_builder.compile()

        return self
