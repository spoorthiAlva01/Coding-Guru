from typing import TypedDict, Optional
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from db import (
    get_session_by_id,
    get_messages_by_session,
    add_message,
    get_hint_level,
    increment_hint_level
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

    review_result: Optional[dict]

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

    if state["route"] == "HINT":
        return "hint"

    if state["route"] == "REVIEW":
        return "review"

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

def hint_node(state: GraphState):

    print("Running hint_node")

    problem = state["problem"]
    latest_code = state["latest_code"]
    user_message = state["user_message"]
    hint_level = get_hint_level(
        state["session_id"]
    )

    llm_messages = [
        {
            "role": "system",
            "content": f"""
You are Coding Guru, an expert coding mentor.

The user is solving:

{problem["title"]}

Problem Statement:
{problem["statement"]}

User's Latest Code:
{latest_code if latest_code else "No code written yet"}

Current Hint Level:
{hint_level}

Give exactly ONE progressive hint.

Rules:
- Hint level 0 → very subtle directional nudge
- Hint level 1 → slightly stronger strategic hint
- Hint level 2+ → more specific implementation guidance

Do NOT give full solution immediately.
Help the user think.
"""
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    response = generate_response(
        llm_messages
    )

    increment_hint_level(
        state["session_id"]
    )

    return {
        "llm_response": response
    }



def review_node(state: GraphState):

    print("Running review_node")

    problem = state["problem"]
    latest_code = state["latest_code"]

    review_prompt = [
        {
            "role": "system",
            "content": f"""
You are an expert coding interviewer.

Review the user's solution.

Problem Title:
{problem["title"]}

Problem Statement:
{problem["statement"]}

User Code:
{latest_code}

Return ONLY valid JSON.

Schema:

{{
    "correctness": "",
    "time_complexity": "",
    "space_complexity": "",
    "feedback": [],
    "score": 0
}}
"""
        }
    ]

    response = generate_response(
        review_prompt
    )

    review = json.loads(response)

    return {
        "review_result": review
    }

def save_review_node(state: GraphState):

    print("Running save_review_node")

    review = state["review_result"]

    save_review(
        session_id=state["session_id"],
        correctness=review["correctness"],
        time_complexity=review["time_complexity"],
        space_complexity=review["space_complexity"],
        feedback=review["feedback"],
        score=review["score"]
    )

    feedback_text = "\n".join(
        f"- {item}"
        for item in review["feedback"]
    )

    response = f"""
Correctness: {review['correctness']}

Time Complexity: {review['time_complexity']}

Space Complexity: {review['space_complexity']}

Score: {review['score']}/10

Suggestions:
{feedback_text}
"""

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
    "hint",
    hint_node
)

graph_builder.add_node(
    "review",
    review_node
)

graph_builder.add_node(
    "save_review",
    save_review_node
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
    "hint",
    "save_message"
)
graph_builder.add_edge(
    "review",
    "save_review"
)

graph_builder.add_edge(
    "save_review",
    "save_message"
)

graph_builder.add_edge(
    "save_message",
    END
)

graph = graph_builder.compile()