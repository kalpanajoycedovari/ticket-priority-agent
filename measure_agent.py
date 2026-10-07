# measure_agent.py
# Checks how often each scoring way agrees with what a human decided.
# This does not call the AI, so it is free and fast.

import csv
import os
import random

import brain

DATA_FOLDER = "data"
TICKETS_PER_BATCH = 6
NUMBER_OF_BATCHES = 200


def load_csv(filename):
    path = os.path.join(DATA_FOLDER, filename)
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


customers_by_id = {r["customer_id"]: r for r in load_csv("customers.csv")}
telemetry_by_ticket = {r["ticket_id"]: r for r in load_csv("telemetry.csv")}
sla_by_ticket = {r["ticket_id"]: r for r in load_csv("sla_ledger.csv")}
human_priority = {
    r["ticket_id"]: int(r["priority_a_human_gave_it"])
    for r in load_csv("ticket_outcomes.csv")
}
tickets = load_csv("tickets.csv")


def build_item(ticket):
    return {
        "case_type": "random",
        "ticket": ticket,
        "customer": customers_by_id[ticket["customer_id"]],
        "telemetry": telemetry_by_ticket[ticket["ticket_id"]],
        "sla": sla_by_ticket[ticket["ticket_id"]],
    }


def pairs_right(places, human):
    """Counts the pairs where the order matches the human decision."""
    right = 0
    total = 0
    ids = list(places)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a = ids[i]
            b = ids[j]
            if human[a] == human[b]:
                continue
            total += 1
            human_puts_a_first = human[a] < human[b]
            order_puts_a_first = places[a] < places[b]
            if human_puts_a_first == order_puts_a_first:
                right += 1
    return right, total


def top_pick_is_right(places, human):
    """Is the ticket placed first one of the most urgent, according to the human?"""
    first = min(places, key=places.get)
    return human[first] == min(human.values())


random.seed(42)

names = []
right_pairs = {}
all_pairs = {}
top_hits = {}

for number in range(NUMBER_OF_BATCHES):
    chosen = random.sample(tickets, TICKETS_PER_BATCH)
    batch = [build_item(t) for t in chosen]
    facts = [brain.read_facts(item) for item in batch]
    ids = [f["id"] for f in facts]
    human = {i: human_priority[i] for i in ids}

    orders = brain.rank_all_four_ways(facts)

    ways = {}
    for name, order in orders.items():
        ways[name] = {i: brain.position_in(order, i) for i in ids}

    shuffled = ids[:]
    random.shuffle(shuffled)
    ways["shuffled (luck only)"] = {i: place for place, i in enumerate(shuffled, start=1)}

    for name, places in ways.items():
        if name not in right_pairs:
            names.append(name)
            right_pairs[name] = 0
            all_pairs[name] = 0
            top_hits[name] = 0
        r, t = pairs_right(places, human)
        right_pairs[name] += r
        all_pairs[name] += t
        if top_pick_is_right(places, human):
            top_hits[name] += 1

print(f"\nBatches: {NUMBER_OF_BATCHES}, tickets per batch: {TICKETS_PER_BATCH}\n")
print(f"{'way':28} {'pairs right':>12} {'top pick right':>16}")
for name in names:
    pairs_percent = 100 * right_pairs[name] / all_pairs[name]
    top_percent = 100 * top_hits[name] / NUMBER_OF_BATCHES
    print(f"{name:28} {pairs_percent:11.1f}% {top_percent:15.1f}%")