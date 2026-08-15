"""
build_demo_batch.py

Picks a small set of tickets from the historical data that argue
with each other, and saves them as the batch we hand to the agent.

We want tickets where the sources point in different directions,
so the agent has a real decision to make rather than an obvious one.
"""

import csv
import os
import json

DATA_FOLDER = "data"


def load_csv(filename):
    """Reads a CSV file and gives back a list of dictionaries, one per row."""
    full_path = os.path.join(DATA_FOLDER, filename)
    with open(full_path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


customers = load_csv("customers.csv")
tickets = load_csv("tickets.csv")
telemetry = load_csv("telemetry.csv")
sla_ledger = load_csv("sla_ledger.csv")

print(f"Loaded {len(tickets)} tickets to choose from.")
# ----- JOIN THE SOURCES ONTO EACH TICKET -----

def build_lookup(rows, key_name):
    """Turns a list of rows into a dictionary we can look things up in quickly."""
    return {row[key_name]: row for row in rows}


customers_by_id = build_lookup(customers, "customer_id")
telemetry_by_ticket = build_lookup(telemetry, "ticket_id")
sla_by_ticket = build_lookup(sla_ledger, "ticket_id")


def enrich(ticket):
    """Gathers everything the three sources know about one ticket."""
    return {
        "ticket": ticket,
        "customer": customers_by_id[ticket["customer_id"]],
        "telemetry": telemetry_by_ticket[ticket["ticket_id"]],
        "sla": sla_by_ticket[ticket["ticket_id"]],
    }


enriched = [enrich(t) for t in tickets]


# ----- HUNTING FOR SPECIFIC ARCHETYPES -----
#
# Each function below asks: is this ticket a good example of one case_type?
# We want the STRONGEST example of each, not just any example.

SEVERITY_ORDER = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def numbers(item):
    """Pulls the values we care about out of the text and converts them."""
    return {
        "value": int(item["customer"]["monthly_value_gbp"]),
        "reported": SEVERITY_ORDER[item["ticket"]["reported_severity"]],
        "observed": SEVERITY_ORDER[item["telemetry"]["observed_severity"]],
        "users": int(item["telemetry"]["affected_users"]),
        "blocked": item["telemetry"]["work_is_blocked"] == "True",
        "hours_left": float(item["sla"]["hours_left_before_promise_broken"]),
        "contacts": int(item["ticket"]["times_contacted_about_this"]),
        "issue": item["ticket"]["issue_type"],
    }


def strongest(candidates, score_function):
    """
    Out of a list of tickets, picks the one that scores highest.
    We use this to get the most extreme example of each case_type.
    """
    if not candidates:
        return None
    return max(candidates, key=score_function)


print(f"Enriched {len(enriched)} tickets.")
# ----- PICKING ONE TICKET PER ARCHETYPE -----

chosen = {}


# 1. RICH BUT TRIVIAL
# A very valuable customer with a problem that barely matters.
# Revenue says handle first, reality says handle last.

candidates = []
for item in enriched:
    n = numbers(item)
    if n["value"] >= 10000 and n["observed"] <= 1 and not n["blocked"]:
        candidates.append(item)

chosen["big_payer_small_problem"] = strongest(candidates, lambda i: numbers(i)["value"])


# 2. POOR BUT BROKEN
# A customer paying nothing whose business has stopped.
# Reality says handle first, revenue says handle last.

candidates = []
for item in enriched:
    n = numbers(item)
    if n["value"] == 0 and n["observed"] >= 4 and n["blocked"]:
        candidates.append(item)

chosen["free_user_big_problem"] = strongest(candidates, lambda i: numbers(i)["users"])


# 3. INVISIBLE TO MONITORING
# A security incident. Every automated signal says ignore this.

candidates = []
for item in enriched:
    n = numbers(item)
    if n["issue"] == "security_incident":
        candidates.append(item)

chosen["hidden_problem"] = strongest(candidates, lambda i: numbers(i)["contacts"])


# 4. THE CLOCK
# Something minor that is about to breach its contract.

candidates = []
for item in enriched:
    n = numbers(item)
    if n["observed"] <= 1 and 0 < n["hours_left"] < 1:
        candidates.append(item)

chosen["deadline_close"] = strongest(candidates, lambda i: numbers(i)["value"])


# 5. REPEATEDLY FAILED
# Someone who has written again and again and we still have not fixed it.

candidates = []
for item in enriched:
    n = numbers(item)
    if n["contacts"] >= 6 and n["hours_left"] < 0:
        candidates.append(item)

chosen["asked_before"] = strongest(candidates, lambda i: numbers(i)["contacts"])


# 6. THE EXAGGERATOR
# Customer ticked Critical. Monitoring sees almost nothing.
# We exclude the problems monitoring is blind to, because a security
# incident marked Critical is accurate, not exaggerated.

blind_spots = ["security_incident", "compliance_request", "data_loss", "billing_error"]

candidates = []
for item in enriched:
    n = numbers(item)
    if n["reported"] >= 4 and n["observed"] <= 1 and n["issue"] not in blind_spots:
        candidates.append(item)

chosen["overstated"] = strongest(candidates, lambda i: -numbers(i)["users"])
# Report what we found.
print("\nChosen tickets:")
for case_type, item in chosen.items():
    if item is None:
        print(f"  {case_type:28} NOT FOUND")
    else:
        t = item["ticket"]
        c = item["customer"]
        m = item["telemetry"]
        print(f"  {case_type:28} {t['ticket_id']}  {t['issue_type']:20} {c['plan']:11} £{c['monthly_value_gbp']:>6}/mo  says {t['reported_severity']:8} monitoring says {m['observed_severity']}")
        # ----- SAVING THE BATCH -----
#
# We save as JSON rather than CSV because each ticket carries nested
# context from three sources, which does not fit neatly into flat columns.

batch = []

for case_type, item in chosen.items():
    if item is None:
        continue

    batch.append({
        "case_type": case_type,
        "ticket": item["ticket"],
        "customer": item["customer"],
        "telemetry": item["telemetry"],
        "sla": item["sla"],
    })

output_path = os.path.join(DATA_FOLDER, "demo_batch.json")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(batch, f, indent=2)

print(f"\nSaved {len(batch)} tickets to {output_path}")