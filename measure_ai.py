# measure_ai.py
# Runs the real AI on random batches and checks how often its order
# agrees with what a human decided. Saves no log files.

import csv
import os
import random
import time

import brain
import decide

DATA_FOLDER = "data"
TICKETS_PER_BATCH = 6
NUMBER_OF_BATCHES = 30


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
    first = min(places, key=places.get)
    return human[first] == min(human.values())


random.seed(42)

names = ["the AI", "damage way", "shuffled (luck only)"]
right_pairs = {n: 0 for n in names}
all_pairs = {n: 0 for n in names}
top_hits = {n: 0 for n in names}
batches_used = 0
batches_failed = 0

for number in range(NUMBER_OF_BATCHES):
    chosen = random.sample(tickets, TICKETS_PER_BATCH)
    batch = [build_item(t) for t in chosen]
    facts = [brain.read_facts(item) for item in batch]
    ids = [f["id"] for f in facts]
    human = {i: human_priority[i] for i in ids}

    try:
        evidence = brain.gather_evidence(batch)
        answer = decide.ask_the_model(evidence)
        order = answer["order"]
    except Exception as problem:
        print(f"Batch {number + 1}: the AI call failed ({problem})")
        batches_failed += 1
        continue

    if sorted(order) != sorted(ids):
        print(f"Batch {number + 1}: the AI left out or invented a ticket, skipped")
        batches_failed += 1
        continue

    orders = brain.rank_all_four_ways(facts)
    shuffled = ids[:]
    random.shuffle(shuffled)

    ways = {
        "the AI": {t: place for place, t in enumerate(order, start=1)},
        "damage way": {i: brain.position_in(orders["damage"], i) for i in ids},
        "shuffled (luck only)": {t: place for place, t in enumerate(shuffled, start=1)},
    }

    for name, places in ways.items():
        r, t = pairs_right(places, human)
        right_pairs[name] += r
        all_pairs[name] += t
        if top_pick_is_right(places, human):
            top_hits[name] += 1

    batches_used += 1
    print(f"Batch {number + 1} done")
    time.sleep(2)

print(f"\nBatches measured: {batches_used}, failed or skipped: {batches_failed}\n")
print(f"{'way':24} {'pairs right':>12} {'top pick right':>16}")
if batches_used > 0:
    for name in names:
        pairs_percent = 100 * right_pairs[name] / all_pairs[name]
        top_percent = 100 * top_hits[name] / batches_used
        print(f"{name:24} {pairs_percent:11.1f}% {top_percent:15.1f}%")