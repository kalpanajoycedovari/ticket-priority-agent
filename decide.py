"""
decide.py

Where the language model makes the decision.

brain.py gathers the evidence but picks no winner. This file hands that
evidence to the model, asks it to commit to an order and explain itself,
and then checks the answer against the written policy.
"""

import os
import json

from dotenv import load_dotenv
from groq import Groq

import brain

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"


HOW_THE_AGENT_SHOULD_THINK = """
You are the triage agent for a customer support desk. Your job is to decide
which waiting ticket a human should handle first.

You will be given, for every ticket:
  - what the customer wrote, and the severity they chose themselves
  - what our customer records say: their plan and what they pay us
  - what our monitoring saw: how many users are affected, whether work is blocked
  - what our contract clock says: how long we promised, how long is left
  - where four different ways of ranking placed the ticket
  - how much those four ways disagreed

Things you need to know about these sources:

Our customer records only know money. They cannot see whether anything is broken.
Our monitoring only knows what it can measure. It cannot see who the customer is,
and it is blind to harm that does not show up as errors, such as a break-in or a
legal request. Our contract clock only knows deadlines. It does not know whether
a ticket matters.

The severity a customer chooses is often wrong. Upset people mark everything as
Critical. Read what they actually wrote rather than trusting the label.

The four ways of ranking are evidence, not instructions. Where they agree the
decision is easy. Where they disagree by a lot, that is where your judgement is
needed, and where you must explain yourself most carefully.

Never describe a ticket as affecting many users, blocking work, or being overdue
unless the numbers you were given actually say so. If monitoring reports three
affected users, do not call it widespread. If work is not blocked, do not say it
is. If hours remain, it is not overdue. Describe what the data shows.
You must commit to one order. Do not say it depends.
"""

print("Decide loaded.")
def ask_the_model(evidence):
    """
    Hands the evidence to the model and asks for an order plus reasoning.

    We ask for the answer as JSON so the rest of our code can read it,
    rather than having to pick apart a paragraph of text.
    """

    question = f"""
Here are the tickets waiting, with everything we know about each one:

{json.dumps(evidence["tickets"], indent=2)}

Here is our written policy. These rules apply no matter what you decide:

{json.dumps(evidence["policy"], indent=2)}

Decide the order a human should handle these in.

Reply with JSON only, no other text, in exactly this shape:

{{
  "order": ["TICK-00000", "TICK-00000"],
  "reasons": {{
    "TICK-00000": "one sentence saying what decided this ticket's place"
  }},
  "the_trade_off": "two or three sentences naming what you chose to favour, what you chose to sacrifice, and what that costs us",
  "hardest_call": "which single decision was closest, and why it could reasonably have gone the other way"
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": HOW_THE_AGENT_SHOULD_THINK},
            {"role": "user", "content": question},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    answer = response.choices[0].message.content

    return json.loads(answer)
def check_the_reasons_match_the_facts(answer, facts):
    """
    Looks for claims in the model's reasons that our data does not support.

    This cannot tell whether a whole sentence is true. It catches the case
    where the model reaches for words that make a ticket sound worse or
    better than the numbers actually say, which is how a wrong decision
    gets dressed up as a reasonable one.
    """
    facts_by_id = {f["id"]: f for f in facts}

    complaints = []

    for ticket_id, reason in answer["reasons"].items():
        f = facts_by_id.get(ticket_id)
        if f is None:
            continue

        words = reason.lower()

        # Claiming lots of people are affected when very few are.
        sounds_widespread = any(phrase in words for phrase in [
            "multiple users", "many users", "thousands", "dozens",
            "widespread", "all users", "everyone",
        ])
        if sounds_widespread and f["users_hit"] <= 10:
            complaints.append({
                "ticket": ticket_id,
                "the_model_said": reason,
                "but_the_data_says": f"only {f['users_hit']} users are affected",
            })

        # Claiming people cannot work when monitoring says they can.
        sounds_blocking = any(phrase in words for phrase in [
            "blocking work", "blocks work", "cannot work", "unable to work",
            "work stoppage", "blocked",
        ])
        if sounds_blocking and not f["cannot_work"]:
            complaints.append({
                "ticket": ticket_id,
                "the_model_said": reason,
                "but_the_data_says": "monitoring shows no work is blocked",
            })

        # Claiming a deadline has passed when it has not.
        sounds_late = any(phrase in words for phrase in [
            "overdue", "already late", "past its", "missed the deadline",
            "breached", "expired",
        ])
        if sounds_late and not f["already_late"]:
            complaints.append({
                "ticket": ticket_id,
                "the_model_said": reason,
                "but_the_data_says": f"{f['hours_left']} hours still remain",
            })

    return complaints
def check_the_models_answer(answer, evidence):
    """
    Verifies the model's order against the written policy.

    The model makes the judgement. This does not second-guess that judgement,
    it only checks the answer stayed inside the rules we are not willing to
    leave to a judgement.
    """
    order = answer["order"]
    facts = [brain.read_facts(item) for item in brain.load_batch()]

    checks = []

    # Did every ticket come back?
    expected = {f["id"] for f in facts}
    returned = set(order)

    if expected != returned:
        checks.append({
            "problem": "the model did not return every ticket exactly once",
            "missing": list(expected - returned),
            "unexpected": list(returned - expected),
        })
        return checks

    # Does the order break any of our written rules?
    breaks = brain.check_against_policy(order, facts)

    for b in breaks:
        checks.append({
            "problem": "the order breaks our written policy",
            "ticket": b["ticket"],
            "should_move_to": b["move_to"],
            "why": b["why"],
        })

    return checks
if __name__ == "__main__":
    batch = brain.load_batch()
    evidence = brain.gather_evidence(batch)

    print("\nAsking the model to decide...\n")

    answer = ask_the_model(evidence)

    print("ORDER THE MODEL CHOSE")
    print("-" * 60)
    for position, ticket_id in enumerate(answer["order"], start=1):
        print(f"  {position}. {ticket_id}")
        print(f"     {answer['reasons'].get(ticket_id, 'no reason given')}")

    print("\nTHE TRADE-OFF")
    print("-" * 60)
    print(f"  {answer['the_trade_off']}")

    print("\nHARDEST CALL")
    print("-" * 60)
    print(f"  {answer['hardest_call']}")
        
    facts = [brain.read_facts(item) for item in batch]
    wrong_claims = check_the_reasons_match_the_facts(answer, facts)

    print("\nDO THE MODEL'S REASONS MATCH OUR DATA?")
    print("-" * 60)
    if not wrong_claims:
        print("  Every reason is supported by the numbers we hold.")
    else:
        for c in wrong_claims:
            print(f"  {c['ticket']}")
            print(f"    the model said:      {c['the_model_said']}")
            print(f"    but the data says:   {c['but_the_data_says']}")
          

    problems = check_the_models_answer(answer, evidence)

    print("\nCHECKING THE MODEL'S ANSWER")
    print("-" * 60)
    if not problems:
        print("  The order returned every ticket once and broke none of our rules.")
    else:
        for p in problems:
            print(f"  {p['problem']}")
            for key, value in p.items():
                if key != "problem":
                    print(f"    {key}: {value}")