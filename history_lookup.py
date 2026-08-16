"""
history_lookup.py

Works out how long each kind of problem usually takes to fix, based on
the 1,000 complaints we have already handled.

This is fair to use when a complaint arrives, because it is about the
KIND of problem, not about this particular one. We are asking "password
resets normally take about two hours", not "this password reset took
two hours", which nobody could know yet.
"""

import os
import csv

DATA_FOLDER = "data"


def load(filename):
    """Reads a CSV file and gives back a list of rows."""
    path = os.path.join(DATA_FOLDER, filename)
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def how_long_each_kind_usually_takes():
    """
    Goes through every past complaint and works out the average time
    to fix, for each kind of problem.

    Returns something like {"password_reset": 31.4, "data_loss": 88.2}
    """
    tickets = load("tickets.csv")
    outcomes = load("ticket_outcomes.csv")

    hours_by_ticket = {
        row["ticket_id"]: float(row["hours_to_resolve"]) for row in outcomes
    }

    collected = {}

    for t in tickets:
        kind = t["issue_type"]
        hours = hours_by_ticket.get(t["ticket_id"])

        if hours is None:
            continue

        collected.setdefault(kind, []).append(hours)

    averages = {}
    for kind, hours_list in collected.items():
        averages[kind] = round(sum(hours_list) / len(hours_list), 1)

    return averages

def what_this_number_means():
    """
    A note to go alongside the averages, so nobody misreads them.

    These are how long we took, not how hard the problem is. A password
    reset does not need 132 hours of work. It needs five minutes of work
    after five days of sitting in a queue. So this measures our own past
    behaviour, not the difficulty of the problem.
    """
    return ("average hours from arrival to resolution for this kind of problem, "
            "across 1,000 past complaints. This reflects how quickly we chose to "
            "act, not how hard the problem is to fix.")
if __name__ == "__main__":
    averages = how_long_each_kind_usually_takes()

    print("\nHow long each kind of problem usually takes to fix:")
    print("-" * 55)
    for kind, hours in sorted(averages.items(), key=lambda x: -x[1]):
        print(f"  {kind:24} {hours:>7} hours on average")