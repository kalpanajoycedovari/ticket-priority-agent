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
    The full agent. Gathers the evidence, asks the model to decide,
    then checks the answer against our policy and against our data.

    Returns the order, the reasoning, and both checks.
    """
    batch = brain.load_batch()
    evidence = brain.gather_evidence(batch)
    facts = [brain.read_facts(item) for item in batch]

    answer = decide.ask_the_model(evidence)

    return {
        "order": answer["order"],
        "reasons": answer["reasons"],
        "the_trade_off": answer["the_trade_off"],
        "hardest_call": answer["hardest_call"],
        "checks": {
            "policy": decide.check_the_models_answer(answer, evidence),
            "reasons_match_data": decide.check_the_reasons_match_the_facts(answer, facts),
        },
    }