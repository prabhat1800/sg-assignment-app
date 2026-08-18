from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .store import TaskStore


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class TaskUpdateRequest(BaseModel):
    completed: bool


app = FastAPI(title="Assignment App", version="0.1.0")
store = TaskStore()

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/tasks")
def list_tasks() -> dict[str, list[dict[str, object]]]:
    return {"items": store.list_tasks()}


@app.post("/api/tasks", status_code=201)
def create_task(payload: TaskCreateRequest) -> dict[str, object]:
    try:
        task = store.add_task(payload.title)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return task


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdateRequest) -> dict[str, object]:
    try:
        task = store.update_task_status(task_id=task_id, completed=payload.completed)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="task not found") from exc

    return task