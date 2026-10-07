# history_search.py
# Finds past tickets that look like a new one, and what a human decided
# for them. It only searches the 800 history tickets, never the 200 test
# tickets, so the agent cannot read the answer to a ticket it is tested on.

import csv
import json
import os
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_FOLDER = "data"


def load_csv(filename):
    path = os.path.join(DATA_FOLDER, filename)
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


with open(os.path.join(DATA_FOLDER, "split.json"), "r", encoding="utf-8") as f:
    SPLIT = json.load(f)

_history_ids = set(SPLIT["history"])
_test_ids = set(SPLIT["test"])

_outcomes = {r["ticket_id"]: r for r in load_csv("ticket_outcomes.csv")}
PAST_TICKETS = [t for t in load_csv("tickets.csv") if t["ticket_id"] in _history_ids]

_past_words = [t["subject"] + " " + t["message"] for t in PAST_TICKETS]
_word_counter = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
_past_numbers = _word_counter.fit_transform(_past_words)


def find_similar_past_tickets(subject, message, how_many=5):
    """Gives back the past tickets closest to what the customer wrote,
    with what a human decided for each."""
    new_numbers = _word_counter.transform([subject + " " + message])
    closeness = cosine_similarity(new_numbers, _past_numbers)[0]
    best_first = closeness.argsort()[::-1][:how_many]

    found = []
    for i in best_first:
        t = PAST_TICKETS[i]
        o = _outcomes[t["ticket_id"]]
        found.append({
            "ticket_id": t["ticket_id"],
            "subject": t["subject"],
            "issue_type": t["issue_type"],
            "priority_a_human_gave_it": int(o["priority_a_human_gave_it"]),
            "hours_to_resolve": float(o["hours_to_resolve"]),
            "what_happened": o["what_happened"],
        })
    return found


# ----- A QUICK TEST on the 200 test tickets -----
# Run this file on its own to see it.

if __name__ == "__main__":
    test_tickets = [t for t in load_csv("tickets.csv") if t["ticket_id"] in _test_ids]

    exact = 0
    within_one = 0
    for t in test_tickets:
        similar = find_similar_past_tickets(t["subject"], t["message"], how_many=5)
        guess = Counter(s["priority_a_human_gave_it"] for s in similar).most_common(1)[0][0]
        real = int(_outcomes[t["ticket_id"]]["priority_a_human_gave_it"])
        exact += guess == real
        within_one += abs(guess - real) <= 1

    most_common_in_history = Counter(
        int(_outcomes[t["ticket_id"]]["priority_a_human_gave_it"]) for t in PAST_TICKETS
    ).most_common(1)[0][0]
    plain_guess_exact = sum(
        int(_outcomes[t["ticket_id"]]["priority_a_human_gave_it"]) == most_common_in_history
        for t in test_tickets
    )

    total = len(test_tickets)
    print(f"\nTest tickets: {total}   History tickets searched: {len(PAST_TICKETS)}")
    print(f"Priority guessed from 5 similar past tickets, exactly right: {100 * exact / total:.1f}%")
    print(f"Priority guessed from 5 similar past tickets, within one level: {100 * within_one / total:.1f}%")
    print(f"Always guessing priority {most_common_in_history}, exactly right: {100 * plain_guess_exact / total:.1f}%")