from langchain.agents import create_agent
from llm.bedrock_client import BedrockClient
from prompts import (
    curriculum_planner_prompt,
    orchestrator_prompt,
    progress_assessment_prompt,
    teacher_prompt,
)
from orchestrator import Orchestrator
from langchain_core.messages import HumanMessage
from rolling_window_middleware import RollingWindowMiddleware
from langchain.agents.middleware import SummarizationMiddleware


def build_workflow():
    llm = BedrockClient().get_core()
    curriculum_planner_agent = create_agent(
        name="curriculum_planner_agent",
        model=llm,
        system_prompt=curriculum_planner_prompt.prompt,
        middleware=[RollingWindowMiddleware(max_tokens=10000)],
    )

    progress_assessment_agent = create_agent(
        name="progress_assessment_agent",
        model=llm,
        system_prompt=progress_assessment_prompt.prompt,
        middleware=[RollingWindowMiddleware(max_tokens=10000)],
    )

    teacher_agent = create_agent(
        name="teacher_agent",
        model=llm,
        system_prompt=teacher_prompt.prompt,
        middleware=[
            SummarizationMiddleware(
                llm,
                trigger=("tokens", 4000),
                keep=("messages", 10),
            )
        ],
    )

    orchestrator = Orchestrator(
        worker_agents=[
            curriculum_planner_agent,
            progress_assessment_agent,
            teacher_agent,
        ],
        orchestrator_prompt=orchestrator_prompt,
    )
    return orchestrator.workflow


if __name__ == "__main__":
    workflow = build_workflow()

    _iterator = workflow.stream(
        {
            "messages": [HumanMessage(content="Hello, how are you?")],
            "previous_node": "START",
        }
    )

    for event in _iterator:
        print(event)
