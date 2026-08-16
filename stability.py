"""
stability.py

Asks a different question from the rest of the project.

decide.py works out what order the complaints should be handled in.
This asks how solid that answer is. If one number had been slightly
different, would the order have changed?

An answer that falls apart when a number moves a little is not one you
should trust as much as an answer that holds.
"""

import copy

import brain


def nudge(facts, ticket_id, what_to_change, new_value):
    """
    Makes a copy of the facts with one number changed.

    We copy rather than edit, so the real facts are never touched.
    """
    changed = copy.deepcopy(facts)

    for f in changed:
        if f["id"] == ticket_id:
            f[what_to_change] = new_value

    return changed


# ----- WHAT WE TRY CHANGING -----
#
# For each complaint we try a handful of small changes, the kind of
# thing that could easily have been slightly different in real life.
# Nothing dramatic. We are asking "was this a close call?", not
# "what if everything were different?"

def things_to_try(f):
    """
    Returns a list of small changes worth testing for one complaint.
    Each one says what to change, the new value, and how to describe it.
    """
    tries = []

    # Fewer or more people affected than we thought.
    if f["users_hit"] > 1:
        fewer = max(1, int(f["users_hit"] * 0.5))
        tries.append({
            "change": "users_hit",
            "to": fewer,
            "described_as": f"only {fewer} people were affected, not {f['users_hit']}",
        })

    more = int(f["users_hit"] * 2) + 5
    tries.append({
        "change": "users_hit",
        "to": more,
        "described_as": f"{more} people were affected, not {f['users_hit']}",
    })

    # Work turns out to be blocked, or turns out not to be.
    tries.append({
        "change": "cannot_work",
        "to": not f["cannot_work"],
        "described_as": ("work was blocked after all" if not f["cannot_work"]
                         else "work was not actually blocked"),
    })

    # A few hours more or less on the clock.
    tries.append({
        "change": "hours_left",
        "to": round(f["hours_left"] - (f["promised_hours"] * 0.25), 1),
        "described_as": "we had a quarter less time left than we thought",
    })

    tries.append({
        "change": "hours_left",
        "to": round(f["hours_left"] + (f["promised_hours"] * 0.25), 1),
        "described_as": "we had a quarter more time left than we thought",
    })

    # The customer pays a bit more or less than recorded.
    if f["pays_monthly"] > 0:
        tries.append({
            "change": "pays_monthly",
            "to": int(f["pays_monthly"] * 0.5),
            "described_as": "this customer pays us half what we thought",
        })

    tries.append({
        "change": "pays_monthly",
        "to": f["pays_monthly"] + 20000,
        "described_as": "this customer pays us £20,000 a month more than recorded",
    })

    return tries


# ----- RUNNING THE TEST -----
#
# We rank the complaints normally, then rank them again with one number
# changed, and see whether the order moved.
#
# We use the four ways of ranking rather than asking the AI again. That
# is on purpose. Asking the AI fifty times would be slow, expensive, and
# the AI varies between runs anyway, so we could not tell whether the
# order moved because of our change or because the AI felt different.
# The four ways give the same answer every time, so anything that moves
# moved because of the change we made.
#
# This means we are measuring how solid the SCORING is, not how solid
# the AI's final answer is. The AI decides on top of the scoring, using
# the customer's own words and our written rules, and this test cannot
# see either of those.

def order_from_the_four_ways(facts):
    """
    Combines the four ways of ranking into one order, so we have
    something steady to compare against.
    """
    orders = brain.rank_all_four_ways(facts)

    counts_for = {
        "damage": 1.5,
        "deadline": 1.0,
        "money": 0.8,
        "fairness": 0.8,
    }

    totals = {}

    for f in facts:
        total = 0
        for way, order in orders.items():
            place = brain.position_in(order, f["id"])
            points = len(facts) + 1 - place
            total = total + (points * counts_for[way])
        totals[f["id"]] = total

    ranked = sorted(facts, key=lambda f: totals[f["id"]], reverse=True)

    return [f["id"] for f in ranked]


def how_solid_is_this(facts):
    """
    For every complaint, tries each small change and records whether
    the order moved.
    """
    normal_order = order_from_the_four_ways(facts)

    results = {}

    for f in facts:
        started_at = brain.position_in(normal_order, f["id"])
        attempts = things_to_try(f)
        moves = []

        for attempt in attempts:
            changed_facts = nudge(facts, f["id"], attempt["change"], attempt["to"])
            new_order = order_from_the_four_ways(changed_facts)
            ended_at = brain.position_in(new_order, f["id"])

            if ended_at != started_at:
                moves.append({
                    "if": attempt["described_as"],
                    "moves_from": started_at,
                    "moves_to": ended_at,
                    "how_far": abs(ended_at - started_at),
                })

        if not moves:
            verdict = "solid"
        elif len(moves) <= 2:
            verdict = "fairly solid"
        else:
            verdict = "shaky"

        results[f["id"]] = {
            "id": f["id"],
            "subject": f["subject"],
            "where_the_scoring_puts_it": started_at,
            "how_solid": verdict,
            "small_changes_that_move_it": len(moves),
            "small_changes_tried": len(attempts),
            "biggest_move": max([m["how_far"] for m in moves], default=0),
            "what_would_move_it": moves,
            "worth_a_second_look": verdict == "shaky",
        }

    return {"order_from_scoring_alone": normal_order, "by_ticket": results}


if __name__ == "__main__":
    batch = brain.load_batch()
    facts = [brain.read_facts(item) for item in batch]

    print("\nTesting how solid each decision is...\n")

    outcome = how_solid_is_this(facts)

    print("HOW SOLID IS EACH DECISION?")
    print("-" * 70)

    for r in outcome["by_ticket"].values():
        print(f"\n  {r['id']}  the scoring puts it at position {r['where_the_scoring_puts_it']}")
        print(f"  {r['subject']}")
        print(f"  {r['small_changes_that_move_it']} of {r['small_changes_tried']} "
              f"small changes move it  ->  {r['how_solid']}")

        for m in r["what_would_move_it"]:
            print(f"    If {m['if']},")
            print(f"      it moves from {m['moves_from']} to {m['moves_to']}")