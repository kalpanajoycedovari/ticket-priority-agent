# measure_compare.py
# The real before and after test.
# Same batches, same tickets, the AI asked twice: once as it is today,
# once with handbook entries and similar past tickets added.
# Only the 200 test tickets are used, which the lookup never searches.
#
# Groq's free plan has a daily limit, so this saves its answers after
# every call. When the limit is hit it stops. Run it again later and it
# carries on from where it stopped.

import copy
import csv
import json
import os
import random
import time

import brain
import decide
import handbook_search
import history_search

DATA_FOLDER = "data"
PROGRESS_FILE = os.path.join(DATA_FOLDER, "compare_progress.json")
TICKETS_PER_BATCH = 6
NUMBER_OF_BATCHES = 30


class DailyLimitReached(Exception):
    pass


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

with open(os.path.join(DATA_FOLDER, "split.json"), "r", encoding="utf-8") as f:
    test_ids = set(json.load(f)["test"])
test_tickets = [t for t in load_csv("tickets.csv") if t["ticket_id"] in test_ids]

# The same 30 batches every time, so a later run continues the same test.
random.seed(42)
all_batches = [random.sample(test_tickets, TICKETS_PER_BATCH) for _ in range(NUMBER_OF_BATCHES)]


def build_item(ticket):
    return {
        "case_type": "random",
        "ticket": ticket,
        "customer": customers_by_id[ticket["customer_id"]],
        "telemetry": telemetry_by_ticket[ticket["ticket_id"]],
        "sla": sla_by_ticket[ticket["ticket_id"]],
    }


def add_the_lookups(evidence):
    """Adds handbook entries and similar past tickets to each ticket."""
    richer = copy.deepcopy(evidence)
    for ticket in richer["tickets"]:
        entries = handbook_search.find_handbook_entries(
            ticket["subject"], ticket["message"], how_many=2)
        ticket["handbook_notes"] = [
            {"title": e["title"], "text": e["text"]} for e in entries]

        similar = history_search.find_similar_past_tickets(
            ticket["subject"], ticket["message"], how_many=3)
        ticket["similar_past_tickets"] = [
            {
                "problem_type": s["issue_type"],
                "priority_a_human_gave_it": s["priority_a_human_gave_it"],
                "hours_to_resolve": s["hours_to_resolve"],
            }
            for s in similar]
    return richer


def ask_and_wait_if_needed(evidence):
    """Asks the AI. If Groq says slow down for a minute, waits and tries again.
    If Groq says the day's allowance is used up, stops."""
    for attempt in range(5):
        try:
            return decide.ask_the_model(evidence)["order"]
        except Exception as problem:
            text = str(problem)
            if "tokens per day" in text or "(TPD)" in text:
                raise DailyLimitReached()
            if "429" in text:
                time.sleep(25)
                continue
            raise
    raise Exception("Groq kept saying slow down")


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f)


progress = load_progress()
already_done = sum(1 for e in progress.values() if "plain" in e and "rich" in e)
print(f"Batches already finished: {already_done} of {NUMBER_OF_BATCHES}")

# ----- ASK THE AI -----

for number in range(NUMBER_OF_BATCHES):
    key = str(number)
    entry = progress.get(key, {})
    if "plain" in entry and "rich" in entry:
        continue

    batch = [build_item(t) for t in all_batches[number]]

    try:
        evidence = brain.gather_evidence(batch)

        if "plain" not in entry:
            entry["plain"] = ask_and_wait_if_needed(evidence)
            progress[key] = entry
            save_progress(progress)
            time.sleep(3)

        if "rich" not in entry:
            entry["rich"] = ask_and_wait_if_needed(add_the_lookups(evidence))
            progress[key] = entry
            save_progress(progress)
            time.sleep(3)

    except DailyLimitReached:
        print("\nGroq's daily allowance is used up. Everything so far is saved.")
        print("Run this file again later and it will carry on from here.")
        break
    except Exception as problem:
        print(f"Batch {number + 1}: failed ({problem})")
        continue

    print(f"Batch {number + 1} done")

# ----- SCORE WHAT WE HAVE -----


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


names = ["AI as it is today", "AI with lookups", "damage way", "shuffled (luck only)"]
right_pairs = {n: 0 for n in names}
all_pairs = {n: 0 for n in names}
top_hits = {n: 0 for n in names}
batches_used = 0
batches_skipped = 0

for number in range(NUMBER_OF_BATCHES):
    entry = progress.get(str(number), {})
    if "plain" not in entry or "rich" not in entry:
        continue

    batch = [build_item(t) for t in all_batches[number]]
    facts = [brain.read_facts(item) for item in batch]
    ids = [f["id"] for f in facts]
    human = {i: human_priority[i] for i in ids}

    if sorted(entry["plain"]) != sorted(ids) or sorted(entry["rich"]) != sorted(ids):
        batches_skipped += 1
        continue

    orders = brain.rank_all_four_ways(facts)
    shuffled = ids[:]
    random.Random(1000 + number).shuffle(shuffled)

    ways = {
        "AI as it is today": {t: p for p, t in enumerate(entry["plain"], start=1)},
        "AI with lookups": {t: p for p, t in enumerate(entry["rich"], start=1)},
        "damage way": {i: brain.position_in(orders["damage"], i) for i in ids},
        "shuffled (luck only)": {t: p for p, t in enumerate(shuffled, start=1)},
    }

    for name, places in ways.items():
        r, t = pairs_right(places, human)
        right_pairs[name] += r
        all_pairs[name] += t
        if top_pick_is_right(places, human):
            top_hits[name] += 1

    batches_used += 1

print(f"\nBatches measured: {batches_used} of {NUMBER_OF_BATCHES}, skipped: {batches_skipped}\n")
print(f"{'way':24} {'pairs right':>12} {'top pick right':>16}")
if batches_used > 0:
    for name in names:
        pairs_percent = 100 * right_pairs[name] / all_pairs[name]
        top_percent = 100 * top_hits[name] / batches_used
        print(f"{name:24} {pairs_percent:11.1f}% {top_percent:15.1f}%")