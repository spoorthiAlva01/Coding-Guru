from db import init_db, create_session
from services.problem_services import get_problem_by_id




init_db()

session = create_session(
    "spoorthi",
    "two-sum"
)
problem = get_problem_by_id("two-sum")

print(problem)

print(dict(session))