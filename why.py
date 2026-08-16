"""
why.py

Answers the question a support manager actually asks months later:
"why did this complaint end up where it did?"

Run it like this:  python why.py TICK-00771
"""

import sys

import decision_log


if len(sys.argv) < 2:
    print("\nTell me which complaint to look up, like this:")
    print("  python why.py TICK-00771\n")

    records = decision_log.load_all_records()
    print(f"There are {len(records)} decisions on record.")

    if records:
        print("\nComplaints you can ask about:")
        for t in records[-1]["tickets"]:
            print(f"  {t['ticket_id']}  {t['subject']}")
    sys.exit()


ticket_id = sys.argv[1].upper()

history = decision_log.why_was_this_ticket_placed_there(ticket_id)

if not history:
    print(f"\nNothing on record for {ticket_id}.")
    sys.exit()

print(f"\n{ticket_id} appears in {len(history)} decision(s).\n")
print("=" * 70)

for h in history:
    print(f"\n  {h['decided_at']}   ({h['decision_id']})")
    print(f"  Placed {h['placed_at']} out of {h['out_of']}")
    print(f"  Reason: {h['reason']}")
    print(f"  How solid that was: {h['how_solid']}")
    if h["needed_a_person"]:
        print("  Flagged for a person to look at.")