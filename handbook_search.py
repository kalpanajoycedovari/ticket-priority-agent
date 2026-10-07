# handbook_search.py
# Looks up the handbook entries that best match a ticket.
# It compares the words in the ticket with the words in each entry
# and gives back the closest ones. No AI call, so it is free and fast.

import csv
import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_FOLDER = "data"

with open(os.path.join(DATA_FOLDER, "handbook.json"), "r", encoding="utf-8") as f:
    HANDBOOK = json.load(f)

# The words in each entry that the search compares against.
_entry_words = [entry["title"] + ". " + entry["text"] for entry in HANDBOOK]
_word_counter = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
_entry_numbers = _word_counter.fit_transform(_entry_words)


def find_handbook_entries(subject, message, how_many=3):
    """Gives back the handbook entries closest to what the customer wrote."""
    ticket_numbers = _word_counter.transform([subject + " " + message])
    closeness = cosine_similarity(ticket_numbers, _entry_numbers)[0]
    best_first = closeness.argsort()[::-1][:how_many]
    return [HANDBOOK[i] for i in best_first]


# ----- A QUICK TEST: does the right entry come back? -----
# Run this file on its own to see it.

if __name__ == "__main__":
    with open(os.path.join(DATA_FOLDER, "tickets.csv"), "r", newline="", encoding="utf-8") as f:
        tickets = list(csv.DictReader(f))

    first_right = 0
    top_three_right = 0
    by_type = {}

    for t in tickets:
        found = find_handbook_entries(t["subject"], t["message"], how_many=3)
        kind = t["issue_type"]

        hit_first = found[0]["about"] == kind
        hit_top_three = any(entry["about"] == kind for entry in found)

        first_right += hit_first
        top_three_right += hit_top_three

        if kind not in by_type:
            by_type[kind] = [0, 0]
        by_type[kind][0] += hit_top_three
        by_type[kind][1] += 1

    total = len(tickets)
    print(f"\nTickets tested: {total}")
    print(f"Right entry came back first:        {100 * first_right / total:.1f}%")
    print(f"Right entry came back in top three: {100 * top_three_right / total:.1f}%")

    print("\nWeakest problem types (right entry in top three):")
    weakest = sorted(by_type.items(), key=lambda pair: pair[1][0] / pair[1][1])[:5]
    for kind, (hits, count) in weakest:
        print(f"  {kind:24} {100 * hits / count:5.1f}%  ({count} tickets)")