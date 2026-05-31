from fastapi import FastAPI
from pydantic import BaseModel
from services.problem_services import get_problem_by_id


from db import (
    init_db,
    get_session,
    create_session,
    update_code,
    get_session_by_id,
    add_message,
    get_messages_by_session
)

from llm import generate_response


app = FastAPI()


init_db()


class StartSessionRequest(BaseModel):
    user_id: str
    problem_id: str

class UpdateCodeRequest(BaseModel):
    session_id: int
    code: str
    
class MentorChatRequest(BaseModel):
    session_id: int
    message: str

@app.post("/sessions/start")
def start_session(request: StartSessionRequest):

    session = get_session(
        request.user_id,
        request.problem_id
    )

    if not session:
        session = create_session(
            request.user_id,
            request.problem_id
        )

    return dict(session)

@app.get("/problems/{problem_id}")
def get_problem(problem_id: str):

    problem = get_problem_by_id(problem_id)

    if not problem:
        return {
            "error": "Problem not found"
        }

    return problem

@app.patch("/sessions/code")
def save_code(request: UpdateCodeRequest):

    session = update_code(
        request.session_id,
        request.code
    )

    return dict(session)

@app.post("/mentor/chat")
def mentor_chat(request: MentorChatRequest):

    # 1. Fetch session
    session = get_session_by_id(request.session_id)

    if not session:
        return {
            "error": "Session not found"
        }

    # 2. Fetch problem
    problem = get_problem_by_id(
        session["problem_id"]
    )

    # 3. Save user message
    add_message(
        request.session_id,
        "user",
        request.message
    )

    # 4. Fetch full chat history
    messages = get_messages_by_session(
        request.session_id
    )

    # 5. Convert DB rows → LLM format
    llm_messages = []

    # system prompt first
    llm_messages.append(
        {
            "role": "system",
            "content": f"""
You are Coding Guru, an AI coding mentor.

Help the user solve this coding problem without directly giving away the answer immediately.

Problem Title: {problem["title"]}

Problem Statement:
{problem["statement"]}

Description:
{problem["description"]}

User's Latest Code:
{session["latest_code"] if session["latest_code"] else "No code written yet"}

Guide the user like a mentor. Ask questions. Give nudges. Encourage problem solving.
"""
        }
    )

    for msg in messages:
        llm_messages.append(
            {
                "role": msg["role"],
                "content": msg["content"]
            }
        )

    # 6. Ask LLM
    response = generate_response(
        llm_messages
    )

    # 7. Save assistant reply
    add_message(
        request.session_id,
        "assistant",
        response
    )

    # 8. Return response
    return {
        "response": response
    }