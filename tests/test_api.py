"""
Tests for the web service in api.py.

FastAPI's test client calls the endpoints directly, without starting a server.
The /decide test swaps the real agent for a pretend one, so no AI call is made.
"""

from fastapi.testclient import TestClient

import api
import brain
import decide

client = TestClient(api.app)


def test_health_says_the_service_is_running():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "running"}


def test_evidence_returns_every_waiting_ticket_and_all_four_orders():
    response = client.get("/evidence")
    assert response.status_code == 200

    body = response.json()
    assert len(body["tickets"]) == len(brain.load_batch())
    assert set(body["orders"].keys()) == {"money", "damage", "deadline", "fairness"}
    assert len(body["policy"]) == 3


def test_decide_hands_back_whatever_the_agent_decided(monkeypatch):
    pretend_answer = {"final_order": ["T1", "T2"]}
    monkeypatch.setattr(decide, "run_the_agent", lambda: pretend_answer)

    response = client.post("/decide")
    assert response.status_code == 200
    assert response.json() == pretend_answer
