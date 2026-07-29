import asyncio
import uuid
from datetime import datetime

_tasks: dict[str, dict] = {}


def create_task() -> str:
    task_id = str(uuid.uuid4())[:8]
    _tasks[task_id] = {
        "logs": [],
        "result": None,
        "done": False,
        "created_at": datetime.now(),
    }
    return task_id


def add_log(task_id: str, message: str):
    task = _tasks.get(task_id)
    if task:
        task["logs"].append(message)


def get_logs(task_id: str) -> list[str]:
    task = _tasks.get(task_id)
    return task["logs"] if task else []


def set_result(task_id: str, result):
    task = _tasks.get(task_id)
    if task:
        task["result"] = result
        task["done"] = True


def get_result(task_id: str):
    task = _tasks.get(task_id)
    if task and task["done"]:
        return task["result"]
    return None


def is_done(task_id: str) -> bool:
    task = _tasks.get(task_id)
    return task["done"] if task else False
