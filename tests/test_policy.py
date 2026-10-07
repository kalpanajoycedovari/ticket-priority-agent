"""
Tests for reading the message and for the severity policy in brain.py.

Each test builds a small made-up queue, runs the check, and looks at
what comes back. No AI calls are used.
"""

import brain


def make_facts(ticket_id, **changes):
    """A plain ticket that breaks no rule. Each test changes only what it needs."""
    facts = {
        "id": ticket_id,
        "subject": "Question",
        "message": "Please help with my invoice.",
        "issue": "billing",
        "pays_monthly": 100,
        "monitoring_says": 1,
        "cannot_work": False,
    }
    facts.update(changes)
    return facts


def make_queue(number_of_filler_tickets, special_ticket):
    """Filler tickets first, then the special ticket last. Returns facts and the order."""
    fillers = [make_facts(f"F{i}") for i in range(1, number_of_filler_tickets + 1)]
    facts = fillers + [special_ticket]
    order = [f["id"] for f in facts]
    return facts, order


# ----- reading the message -----

def test_message_with_a_serious_phrase_is_marked_serious():
    ticket = make_facts("A", message="We think there was a breach on our account.")
    assert "sounds serious" in brain.read_the_message(ticket)


def test_message_about_cancelling_is_marked_as_may_leave():
    ticket = make_facts("A", message="We are considering cancelling next month.")
    assert "may be about to leave" in brain.read_the_message(ticket)


def test_plain_message_gets_no_notes():
    ticket = make_facts("A")
    assert brain.read_the_message(ticket) == []


# ----- the policy -----

def test_break_in_ranked_too_low_is_flagged():
    special = make_facts(
        "S", issue="security_incident", pays_monthly=500,
        message="We saw logins from a country we do not work in.",
    )
    facts, order = make_queue(4, special)   # the break-in sits in position 5
    problems = brain.check_against_policy(order, facts)
    assert len(problems) == 1
    assert problems[0]["ticket"] == "S"
    assert problems[0]["move_to"] == 3


def test_break_in_ranked_high_enough_is_not_flagged():
    special = make_facts(
        "S", issue="security_incident", pays_monthly=500,
        message="We saw logins from a country we do not work in.",
    )
    facts, order = make_queue(4, special)
    order = ["S"] + [i for i in order if i != "S"]   # move it to position 1
    assert brain.check_against_policy(order, facts) == []


def test_legal_request_ranked_too_low_is_flagged():
    special = make_facts("L", issue="compliance_request", pays_monthly=500)
    facts, order = make_queue(4, special)   # position 5, but the limit is 4
    problems = brain.check_against_policy(order, facts)
    assert len(problems) == 1
    assert problems[0]["ticket"] == "L"
    assert problems[0]["move_to"] == 4


def test_badly_affected_free_customer_ranked_last_is_flagged():
    special = make_facts("P", pays_monthly=0, monitoring_says=3)
    facts, order = make_queue(5, special)   # position 6, but the limit is 5
    problems = brain.check_against_policy(order, facts)
    assert len(problems) == 1
    assert problems[0]["ticket"] == "P"
    assert problems[0]["move_to"] == 5


def test_free_customer_with_a_small_problem_is_not_flagged():
    special = make_facts("P", pays_monthly=0, monitoring_says=1)
    facts, order = make_queue(5, special)
    assert brain.check_against_policy(order, facts) == []
