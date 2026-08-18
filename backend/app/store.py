from __future__ import annotations

from dataclasses import dataclass, asdict
from threading import Lock
from typing import Any


@dataclass
class Task:
    id: int
    title: str
    completed: bool


class TaskStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._tasks: list[Task] = []
        self._next_id = 1

    def list_tasks(self) -> list[dict[str, Any]]:
        with self._lock:
            return [asdict(task) for task in self._tasks]

    def add_task(self, title: str) -> dict[str, Any]:
        normalized = title.strip()
        if not normalized:
            raise ValueError("title must not be empty")

        with self._lock:
            task = Task(id=self._next_id, title=normalized, completed=False)
            self._tasks.append(task)
            self._next_id += 1
            return asdict(task)

    def update_task_status(self, task_id: int, completed: bool) -> dict[str, Any]:
        with self._lock:
            for task in self._tasks:
                if task.id == task_id:
                    task.completed = completed
                    return asdict(task)

        raise KeyError(task_id)