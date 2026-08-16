"""
decide_new.py

Runs the agent against a batch that was built from complaints people
actually wrote, rather than the six we picked out of the practice data.

This is the honest test. The agent has never seen these tickets, and the
wording is nothing like the wording in the practice data.
"""

import brain
import decide

# Point the agent at the new batch instead of the usual one.
real_load = brain.load_batch
brain.load_batch = lambda *a, **k: real_load("new_batch.json")

if __name__ == "__main__":
    batch = brain.load_batch()
    print(f"\n{len(batch)} complaints, written by people, never seen before.")
    print("Asking the agent to decide...")
    decide.print_the_result(decide.run_the_agent())