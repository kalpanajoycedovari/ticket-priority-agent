"""
api.py

Puts the ticket prioritisation agent behind a web address so that
n8n, or anything else, can send it tickets and get back an answer.

Run it with:  uvicorn api:app --reload --port 8020
Then open:    http://127.0.0.1:8020/docs
"""

from fastapi import FastAPI

import brain
import decide

app = FastAPI(
    title="Ticket Prioritisation Agent",
    description="Decides which support ticket a human should handle first "
                "when the different sources of information disagree.",
)


@app.get("/health")
def health():
    """A simple check that the service is running."""
    return {"status": "running"}


@app.get("/evidence")
def evidence():
    """
    Gathers everything we know about the waiting tickets and hands it back.

    This makes no decision. It pulls together the three sources, runs the
    four ways of ranking, and reads the messages, so that whoever decides
    next has all the evidence in one place.
    """
    batch = brain.load_batch()
    return brain.gather_evidence(batch)
@app.post("/decide")
def make_a_decision():
    """
    The full agent. Gathers the evidence, asks the model to decide, corrects
    any reason the data does not support, then checks the order against
    our written policy.
    """
    return decide.run_the_agent()