from fastapi import FastAPI
from pydantic import BaseModel
from services.problem_services import get_problem_by_id

from db import (
    init_db,
    get_session,
    create_session,
    update_code
)



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