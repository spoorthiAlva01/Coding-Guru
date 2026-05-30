import json


PROBLEMS_FILE = "data/problems.json"


def get_problem_by_id(problem_id):

    with open(PROBLEMS_FILE, "r") as file:
        problems = json.load(file)

    for problem in problems:
        if problem["id"] == problem_id:
            return problem

    return None