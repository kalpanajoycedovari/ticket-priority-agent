"""
decision_log.py

Keeps a record of every decision the agent makes.

Without this, a decision is made, printed to the screen, and gone. Nobody
can ever go back and ask why a customer was put fourth six months ago.

Each decision is saved as its own file, with everything that went into it:
what was known, what the four ways of ranking said, what the AI chose, why
it said it chose that, what the checks found, and whether a person needs
to look at it.
"""

import os
import json
from datetime import datetime

LOG_FOLDER = os.path.join("data", "decisions")


def make_a_decision_id():
    """
    Builds an id from the date and time, so decisions sort in order
    and no two ever have the same name.
    """
    return "DEC-" + datetime.now().strftime("%Y%m%d-%H%M%S")


print("Decision log loaded.")
def build_the_record(result, facts, orders):
    """
    Puts together everything worth keeping about one decision.

    We save what the agent knew, not just what it chose, so somebody
    reading this later can work out whether the choice was reasonable
    given what was in front of it at the time.
    """
    facts_by_id = {f["id"]: f for f in facts}

    per_ticket = []

    for position, ticket_id in enumerate(result["order"], start=1):
        f = facts_by_id[ticket_id]
        solid = result["how_solid_the_scoring_is"].get(ticket_id, {})

        per_ticket.append({
            "ticket_id": ticket_id,
            "subject": f["subject"],
            "placed_at": position,

            "what_we_knew": {
                "customer_pays_monthly_gbp": f["pays_monthly"],
                "customer_plan": f["plan"],
                "times_they_have_asked": f["times_asked"],
                "monitoring_severity": f["monitoring_says"],
                "people_affected": f["users_hit"],
                "work_is_blocked": f["cannot_work"],
                "hours_promised": f["promised_hours"],
                "hours_left": f["hours_left"],
                "already_late": f["already_late"],
                "customer_claimed_severity": f["customer_says"],
            },

            "where_each_way_of_ranking_put_it": {
                name: order.index(ticket_id) + 1 for name, order in orders.items()
            },

            "why_it_was_placed_there": result["reasons"].get(ticket_id, ""),

            "how_solid": solid.get("how_solid", "not tested"),
            "what_would_move_it": solid.get("what_would_move_it", []),
            "needs_a_person_to_look": solid.get("worth_a_second_look", False),
        })

    return {
        "decision_id": make_a_decision_id(),
        "decided_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "how_many_tickets": len(result["order"]),

        "final_order": result["order"],
        "the_trade_off_made": result["the_trade_off"],
        "hardest_call": result["hardest_call"],
        "which_way_it_leaned_towards": result["strategy_choice"],

        "checks": result["checks"],
        "reasons_before_correction": result.get("reasons_before_correction", {}),

        "tickets": per_ticket,
    }
def save_the_record(record):
    """Writes one decision to its own file and returns where it went."""
    os.makedirs(LOG_FOLDER, exist_ok=True)

    path = os.path.join(LOG_FOLDER, record["decision_id"] + ".json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    return path


def load_all_records():
    """Reads back every decision we have ever saved, oldest first."""
    if not os.path.isdir(LOG_FOLDER):
        return []

    records = []

    for name in sorted(os.listdir(LOG_FOLDER)):
        if name.endswith(".json"):
            with open(os.path.join(LOG_FOLDER, name), encoding="utf-8") as f:
                records.append(json.load(f))

    return records


def why_was_this_ticket_placed_there(ticket_id):
    """
    Looks back through every saved decision for one complaint,
    and explains what happened to it each time.

    This is the question a support manager actually asks six months later.
    """
    found = []

    for record in load_all_records():
        for t in record["tickets"]:
            if t["ticket_id"] == ticket_id:
                found.append({
                    "decision_id": record["decision_id"],
                    "decided_at": record["decided_at"],
                    "placed_at": t["placed_at"],
                    "out_of": record["how_many_tickets"],
                    "reason": t["why_it_was_placed_there"],
                    "how_solid": t["how_solid"],
                    "needed_a_person": t["needs_a_person_to_look"],
                })

    return found