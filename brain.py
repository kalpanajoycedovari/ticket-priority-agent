"""
brain.py

The thinking part of the agent, kept separate from the printing.

agent.py prints things to the screen. api.py serves things over the web.
Both of them need the same decisions made, so those decisions live here
and neither file has its own copy.
"""

import json
import os

DATA_FOLDER = "data"

SEVERITY_ORDER = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def load_batch():
    """Reads the tickets we saved earlier."""
    path = os.path.join(DATA_FOLDER, "demo_batch.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_facts(item):
    """Gathers the facts about one ticket from all three sources."""
    t = item["ticket"]
    c = item["customer"]
    m = item["telemetry"]
    s = item["sla"]

    return {
        "id": t["ticket_id"],
        "subject": t["subject"],
        "message": t["message"],
        "issue": t["issue_type"],
        "customer_says": SEVERITY_ORDER[t["reported_severity"]],
        "times_asked": int(t["times_contacted_about_this"]),

        "company": c["company_name"],
        "plan": c["plan"],
        "pays_monthly": int(c["monthly_value_gbp"]),

        "monitoring_says": SEVERITY_ORDER[m["observed_severity"]],
        "users_hit": int(m["affected_users"]),
        "cannot_work": m["work_is_blocked"] == "True",

        "promised_hours": float(s["promised_response_hours"]),
        "hours_left": float(s["hours_left_before_promise_broken"]),
        "already_late": s["promise_was_broken"] == "True",
    }


print("Brain loaded.")
# ----- THE FOUR WAYS OF RANKING -----

def score_by_money(f):
    """Higher score means handle sooner. Favours whoever pays the most."""
    score = f["pays_monthly"]

    if f["times_asked"] >= 3:
        score = score * 1.2

    return score


def score_by_damage(f):
    """Higher score means handle sooner. Favours real technical harm."""
    score = f["monitoring_says"] * 100
    score = score + (f["users_hit"] / 10)

    if f["cannot_work"]:
        score = score + 150

    return score


def score_by_deadline(f):
    """Higher score means handle sooner. Favours whatever breaks its promise first."""
    if f["already_late"]:
        return 1000 + abs(f["hours_left"])

    share_left = f["hours_left"] / f["promised_hours"]

    return 100 - (share_left * 100)


def score_by_fairness(f):
    """Higher score means handle sooner. Favours people we have treated worst."""
    score = 0
    score = score + (f["times_asked"] * 30)

    if f["already_late"]:
        score = score + 100
        score = score + abs(f["hours_left"])

    if f["pays_monthly"] < 200:
        score = score + 50

    return score


def rank_all_four_ways(facts):
    """
    Runs each way of ranking and returns the four orders,
    as lists of ticket ids with the most urgent first.
    """
    ways = {
        "money": score_by_money,
        "damage": score_by_damage,
        "deadline": score_by_deadline,
        "fairness": score_by_fairness,
    }

    orders = {}
    for name, score_function in ways.items():
        ordered = sorted(facts, key=score_function, reverse=True)
        orders[name] = [f["id"] for f in ordered]

    return orders


def position_in(order, ticket_id):
    """Where does this ticket sit in that order? 1 means first."""
    return order.index(ticket_id) + 1
# ----- READING WHAT THE CUSTOMER WROTE -----

SERIOUS_WORDS = [
    "logins from a country", "did not start", "changed our admin email",
    "was not us", "breach", "missing", "vanished", "gone", "deleted",
    "personal data", "gdpr",
]

LEAVING_WORDS = [
    "considering cancelling", "cancel", "third time", "unacceptable",
]


def read_the_message(f):
    """Looks for things in the message that the numbers cannot show."""
    words = (f["subject"] + " " + f["message"]).lower()

    found = []

    for phrase in SERIOUS_WORDS:
        if phrase in words:
            found.append("sounds serious")
            break

    for phrase in LEAVING_WORDS:
        if phrase in words:
            found.append("may be about to leave")
            break

    return found


# ----- THE SEVERITY POLICY -----
#
# The written rule book. Certain tickets get a guaranteed place in the
# queue no matter what the scoring or the model says, because the
# consequence of getting them wrong is not something we are willing
# to leave to a judgement.

SEVERITY_POLICY = [
    {
        "applies_to": "a suspected break-in or account takeover",
        "must_be_ranked_at_or_above": 3,
        "reason": "monitoring cannot measure this kind of harm, so the numbers "
                  "will always underrate it",
    },
    {
        "applies_to": "a legal request such as GDPR",
        "must_be_ranked_at_or_above": 4,
        "reason": "the deadline is set by law, not by us, and missing it carries a fine",
    },
    {
        "applies_to": "a customer who is badly affected but pays nothing",
        "must_be_ranked_at_or_above": 5,
        "reason": "paying nothing is not a reason to be left last when the problem "
                  "is real. This rule only ever lifts a ticket up the queue. "
                  "It must never be used to push a ticket down.",
    },
]


def check_against_policy(order, facts):
    """
    Looks at an order and returns anything that breaks the policy.
    The order is a list of ticket ids, most urgent first.
    """
    facts_by_id = {f["id"]: f for f in facts}

    breakin_rule = SEVERITY_POLICY[0]
    legal_rule = SEVERITY_POLICY[1]
    unfair_rule = SEVERITY_POLICY[2]

    problems = []

    for position, ticket_id in enumerate(order, start=1):
        f = facts_by_id[ticket_id]
        notes = read_the_message(f)

        if "sounds serious" in notes and f["issue"] == "security_incident":
            if position > breakin_rule["must_be_ranked_at_or_above"]:
                problems.append({
                    "ticket": ticket_id,
                    "move_to": breakin_rule["must_be_ranked_at_or_above"],
                    "why": breakin_rule["reason"],
                })

        if f["issue"] == "compliance_request":
            if position > legal_rule["must_be_ranked_at_or_above"]:
                problems.append({
                    "ticket": ticket_id,
                    "move_to": legal_rule["must_be_ranked_at_or_above"],
                    "why": legal_rule["reason"],
                })

        if position > unfair_rule["must_be_ranked_at_or_above"] and f["pays_monthly"] == 0:
            if f["monitoring_says"] >= 3 or f["cannot_work"]:
                problems.append({
                    "ticket": ticket_id,
                    "move_to": unfair_rule["must_be_ranked_at_or_above"],
                    "why": unfair_rule["reason"],
                })
    return problems
# ----- PULLING IT ALL TOGETHER -----
def severity_as_word(number):
    """Turns 1 to 4 back into a word, so a reader does not have to guess."""
    return {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}[number]
def gather_evidence(batch):
    """
    Takes the raw tickets, works out everything we know about them,
    and hands back a tidy package.

    This is deliberately NOT a decision. It is the evidence file that
    gets handed to whoever makes the decision, whether that is our
    scoring, a language model, or a person.
    """
    facts = [read_facts(item) for item in batch]
    orders = rank_all_four_ways(facts)

    tickets = []

    for f in facts:
        places = {name: position_in(order, f["id"]) for name, order in orders.items()}
        gap = max(places.values()) - min(places.values())

        tickets.append({
            "id": f["id"],
            "subject": f["subject"],
            "message": f["message"],
            "issue_type": f["issue"],

            "customer": {
                "company": f["company"],
                "plan": f["plan"],
                "pays_monthly_gbp": f["pays_monthly"],
                "times_asked": f["times_asked"],
            },
            "monitoring": {
                "severity": severity_as_word(f["monitoring_says"]),
                "users_affected": f["users_hit"],
                "work_is_blocked": f["cannot_work"],
            },
            "deadline": {
                "promised_hours": f["promised_hours"],
                "hours_left": f["hours_left"],
                "already_late": f["already_late"],
            },

            "customer_claimed_severity": severity_as_word(f["customer_says"]),
            "ranked_position_by": places,
            "how_much_the_ways_disagree": gap,
            "notes_from_the_message": read_the_message(f),
        })

    return {
        "tickets": tickets,
        "orders": orders,
        "policy": SEVERITY_POLICY,
    }