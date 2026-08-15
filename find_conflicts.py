"""
find_conflicts.py

Reads the CSV files we generated and finds the tickets where the
different sources disagree with each other most sharply.
These are the tickets worth putting in front of the agent.
"""

import csv
import os

DATA_FOLDER = "data"


def load_csv(filename):
    """
    Reads a CSV file and gives back a list of dictionaries,
    one dictionary per row. Column headings become the keys.
    """
    full_path = os.path.join(DATA_FOLDER, filename)

    with open(full_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} rows from {full_path}")
    return rows


# Load all five files so we can look at them together.
customers = load_csv("customers.csv")
tickets = load_csv("tickets.csv")
telemetry = load_csv("telemetry.csv")
sla_ledger = load_csv("sla_ledger.csv")
outcomes = load_csv("ticket_outcomes.csv")
# ----- JOINING THE SOURCES TOGETHER -----
#
# Right now the files are separate. We want one object per ticket
# carrying everything we know about it, gathered from all sources.


def build_lookup(rows, key_name):
    """
    Turns a list of rows into a dictionary you can look things up in.
    Instead of searching the whole list every time, we go straight to the row.

    So build_lookup(customers, "customer_id") gives us something where
    lookup["CUST-0007"] hands back that customer's row instantly.
    """
    lookup = {}
    for row in rows:
        lookup[row[key_name]] = row
    return lookup


customers_by_id = build_lookup(customers, "customer_id")
telemetry_by_ticket = build_lookup(telemetry, "ticket_id")
sla_by_ticket = build_lookup(sla_ledger, "ticket_id")
outcomes_by_ticket = build_lookup(outcomes, "ticket_id")


def enrich_ticket(ticket):
    """
    Takes one ticket and gathers the context from every source.
    This is the step the brief calls "gather context from independent sources".
    """
    ticket_id = ticket["ticket_id"]
    customer_id = ticket["customer_id"]

    return {
        "ticket": ticket,
        "customer": customers_by_id[customer_id],
        "telemetry": telemetry_by_ticket[ticket_id],
        "sla": sla_by_ticket[ticket_id],
        "outcome": outcomes_by_ticket[ticket_id],
    }


# Do this for every ticket.
enriched = [enrich_ticket(t) for t in tickets]

print(f"\nEnriched {len(enriched)} tickets with context from all sources.")

# Show one so you can see the shape.
example = enriched[0]
print("\nExample of one enriched ticket:")
print(f"  Ticket:    {example['ticket']['ticket_id']} | {example['ticket']['issue_type']} | customer says {example['ticket']['reported_severity']}")
print(f"  Customer:  {example['customer']['company_name']} | {example['customer']['plan']} | £{example['customer']['monthly_value_gbp']}/month")
print(f"  Telemetry: {example['telemetry']['affected_users']} users affected | monitoring says {example['telemetry']['observed_severity']}")
print(f"  SLA:       promised {example['sla']['promised_response_hours']}h | replied in {example['sla']['first_reply_hours']}h")
print(f"  Outcome:   human gave it priority {example['outcome']['priority_a_human_gave_it']}")
# ----- FINDING AND NAMING THE CONFLICTS -----

# Reminder: everything loaded from CSV comes back as TEXT.
# So we convert to numbers before comparing.

SEVERITY_ORDER = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def find_conflicts_in(item):
    """
    Looks at one enriched ticket and returns a list of the
    disagreements found between the different sources.
    """
    ticket = item["ticket"]
    customer = item["customer"]
    telemetry = item["telemetry"]
    sla = item["sla"]

    conflicts = []

    # Convert the text into things we can compare.
    reported = SEVERITY_ORDER[ticket["reported_severity"]]
    observed = SEVERITY_ORDER[telemetry["observed_severity"]]
    monthly_value = int(customer["monthly_value_gbp"])
    affected_users = int(telemetry["affected_users"])
    hours_left = float(sla["hours_left_before_promise_broken"])
    work_is_blocked = telemetry["work_is_blocked"] == "True"
    times_contacted = int(ticket["times_contacted_about_this"])

    # 1. The customer is shouting louder than the evidence supports.
    if reported >= observed + 2:
        conflicts.append("customer_exaggerating")

    # 2. Something serious is happening but the customer has understated it.
    if observed >= reported + 2:
        conflicts.append("customer_understating")

    # 3. Valuable customer, trivial problem. Money says top, reality says bottom.
    if monthly_value >= 3000 and observed <= 2:
        conflicts.append("rich_but_trivial")

    # 4. Customer pays nothing but is completely stuck. Reality says top, money says bottom.
    if monthly_value == 0 and (observed >= 3 or work_is_blocked):
        conflicts.append("poor_but_broken")

    # 5. The clock is about to run out on something minor.
    # We compare against a SHARE of the promise rather than a fixed number of hours,
    # because 1 hour left is relaxed for a free user and nearly over for Enterprise.
    promised_hours = float(sla["promised_response_hours"])
    running_out = hours_left < (promised_hours * 0.2)

    if running_out and observed <= 2:
        conflicts.append("clock_pressure_on_trivial")
    # 6. Real danger that monitoring cannot see at all.
    if ticket["issue_type"] in ["security_incident", "data_loss", "compliance_request"]:
        conflicts.append("invisible_to_monitoring")

   # 7. They have written repeatedly and we still have not fixed it.
    if times_contacted >= 7:
        conflicts.append("repeatedly_failed")

    # 8. We already broke our promise on this one.
    if sla["promise_was_broken"] == "True":
        conflicts.append("promise_already_broken")

    return conflicts
# Run it across everything and count what we found.
conflict_counts = {}

for item in enriched:
    item["conflicts"] = find_conflicts_in(item)
    for name in item["conflicts"]:
        conflict_counts[name] = conflict_counts.get(name, 0) + 1

print("\nConflict types found across the dataset:")
for name, count in sorted(conflict_counts.items(), key=lambda x: -x[1]):
    print(f"  {name:30} {count}")
    # ----- LOOKING AT REAL EXAMPLES -----


def describe(item):
    """Prints one enriched ticket in a readable way."""
    t = item["ticket"]
    c = item["customer"]
    m = item["telemetry"]
    s = item["sla"]

    print(f"\n  {t['ticket_id']}  |  {t['issue_type']}")
    print(f"    Customer says:  {t['reported_severity']}  (mood: {t['customer_mood']})")
    print(f"    Monitoring says: {m['observed_severity']}  ({m['affected_users']} users affected)")
    print(f"    Account:        {c['company_name']}, {c['plan']}, £{c['monthly_value_gbp']}/month")
    print(f"    Clock:          promised {s['promised_response_hours']}h, replied in {s['first_reply_hours']}h")
    print(f"    Message:        {t['message']}")
    print(f"    Conflicts:      {', '.join(item['conflicts'])}")


def show_examples_of(conflict_name, how_many=2):
    """Finds tickets carrying a particular conflict and prints a few."""
    matching = [item for item in enriched if conflict_name in item["conflicts"]]

    print(f"\n{'=' * 70}")
    print(f"{conflict_name.upper()}  ({len(matching)} found)")
    print("=" * 70)

    for item in matching[:how_many]:
        describe(item)


# Show the two archetypes the brief names directly.
show_examples_of("rich_but_trivial", how_many=5)
show_examples_of("poor_but_broken", how_many=5)
show_examples_of("invisible_to_monitoring", how_many=3)