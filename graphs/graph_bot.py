from typing import TypedDict, Optional
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END

from db import (
    get_session_by_id,
    get_messages_by_session
)

from services.problem_services import get_problem_by_id


class GraphState(TypedDict):
    session_id: int

    user_message: str

    problem: Optional[dict]

    latest_code: Optional[str]

    messages: Optional[list]

    route: Optional[str]

    llm_response: Optional[str]

def load_context_node(state: GraphState):

    print("Running load_context_node")

    session = get_session_by_id(
        state["session_id"]
    )

    problem = get_problem_by_id(
        session["problem_id"]
    )

    messages = get_messages_by_session(
        state["session_id"]
    )

    llm_messages = []

    for msg in messages:
        llm_messages.append(
            {
                "role": msg["role"],
                "content": msg["content"]
            }
        )

    return {
        "problem": problem,
        "latest_code": session["latest_code"],
        "messages": llm_messages
    }



from llm import generate_response


def router_node(state: GraphState):

    print("Running router_node")

    user_message = state["user_message"]

    router_prompt = [
        {
            "role": "system",
            "content": """
You are a routing assistant.

Classify the user's intent into exactly one of:

MENTOR
HINT
REVIEW

Reply with only one word:
MENTOR
HINT
or REVIEW
"""
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    route = generate_response(
        router_prompt
    ).strip().upper()

    return {
        "route": route
    }

def route_decision(state: GraphState):

    if state["route"] == "MENTOR":
        return "mentor"

    return "mentor"

def mentor_node(state: GraphState):

    print("Running mentor_node")

    problem = state["problem"]
    latest_code = state["latest_code"]
    messages = state["messages"]
    user_message = state["user_message"]

    llm_messages = [
        {
            "role": "system",
            "content": f"""
You are Coding Guru, an expert coding mentor.

Help the user solve the problem without immediately giving away the full answer.

Problem Title: {problem["title"]}

Problem Statement:
{problem["statement"]}

Description:
{problem["description"]}

User's Latest Code:
{latest_code if latest_code else "No code written yet"}

Guide the user with hints, questions, and nudges.
Encourage thinking instead of directly solving.
"""
        }
    ]

    llm_messages.extend(messages)

    llm_messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    response = generate_response(
        llm_messages
    )

    return {
        "llm_response": response
    }


def save_message_node(state: GraphState):

    print("Running save_message_node")

    add_message(
        state["session_id"],
        "assistant",
        state["llm_response"]
    )

    return state


graph_builder = StateGraph(GraphState)

graph_builder.add_node(
    "load_context",
    load_context_node
)

graph_builder.add_node(
    "router",
    router_node
)

graph_builder.add_node(
    "mentor",
    mentor_node
)

graph_builder.add_node(
    "save_message",
    save_message_node
)


graph_builder.add_edge(
    START,
    "load_context"
)

graph_builder.add_edge(
    "load_context",
    "router"
)

graph_builder.add_conditional_edges(
    "router",
    route_decision
)
graph_builder.add_edge(
    "mentor",
    "save_message"
)

graph_builder.add_edge(
    "save_message",
    END
)

graph = graph_builder.compile()