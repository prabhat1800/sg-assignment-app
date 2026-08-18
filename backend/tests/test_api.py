from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    api_response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_and_list_tasks() -> None:
    create = client.post("/api/tasks", json={"title": "Write assignment README"})
    assert create.status_code == 201
    assert create.json()["title"] == "Write assignment README"
    assert create.json()["completed"] is False

    listed = client.get("/api/tasks")
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert any(task["title"] == "Write assignment README" for task in items)


def test_update_task_completion() -> None:
    create = client.post("/api/tasks", json={"title": "Backend App created"})
    assert create.status_code == 201
    task_id = create.json()["id"]

    updated = client.patch(f"/api/tasks/{task_id}", json={"completed": True})
    assert updated.status_code == 200
    assert updated.json()["completed"] is True