"""
decide.py

Where the language model makes the decision.

brain.py gathers the evidence but picks no winner. This file hands that
evidence to the model, asks it to commit to an order and explain itself,
then checks the answer two ways: against our written policy, and against
the numbers we actually hold.
"""

import os
import json

from dotenv import load_dotenv
from groq import Groq

import brain
import stability
import decision_log
import thinking_log

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"


HOW_THE_AGENT_SHOULD_THINK = """
You are the agent for a customer support desk. Your job is to decide which
waiting ticket a human should handle first.

You will be given, for every ticket:
  - what the customer wrote, and the severity they chose themselves
  - what our customer records say: their plan and what they pay us
  - what our monitoring saw: how many users are affected, whether work is blocked
  - what our contract clock says: how long we promised, how long is left
  - how long we have historically taken on this kind of problem
  - how loaded the system was when the complaint arrived
  - where four different ways of ranking placed the ticket
  - how much those four ways disagreed

Things you need to know about these sources:

Our customer records only know money. They cannot see whether anything is broken.
Our monitoring only knows what it can measure. It cannot see who the customer is,
and it is blind to harm that does not show up as errors, such as a break-in or a
legal request. Our contract clock only knows deadlines. It does not know whether
a ticket matters.

The history figure is how long we took in the past, not how hard the problem is.
A password reset does not need a hundred hours of work. It needs five minutes of
work after five days of being ignored. So a long history number is a sign of how
we have behaved, not a reason to keep behaving that way.

The severity a customer chooses is often wrong. Upset people mark everything as
Critical. Read what they actually wrote rather than trusting the label.

The four ways of ranking are evidence, not instructions. Where they agree the
decision is easy. Where they disagree by a lot, that is where your judgement is
needed, and where you must explain yourself most carefully.

Never describe a ticket as affecting many users, blocking work, or being overdue
unless the numbers you were given actually say so. If monitoring reports three
affected users, do not call it widespread. If work is not blocked, do not say it
is. If hours remain, it is not overdue.

But a reason must still be a reason. Say why the ticket sits where it does, not
just what the numbers are. Listing figures back at us is not an explanation.

Before you decide, look for places where the sources contradict each other, or
where what the customer wrote does not match what monitoring measured. List
those. For each one say which signal you believed and why that source was the
more trustworthy one for that particular complaint.

You must commit to one order. Do not say it depends.

Your order must be your own judgement, not a copy of any of the four rankings.
They are evidence to weigh, not options to pick from.

After you have decided, rank all four ways of ranking from 1 to 4, where 1 is the
one that deserved the most weight for this particular batch of complaints. Give
every one of the four a place. For each, say why it sits where it does and what
it gets wrong. Every one of them is reasonable and every one has a drawback, so
name the drawback of your first place rather than pretending it has none.
"""


def ask_the_model(evidence):
    """
    Hands the evidence to the model and asks for an order plus reasoning.

    We ask for the answer as JSON so the rest of our code can read it,
    rather than having to pick apart a paragraph of text.
    """
    question = f"""
Here are the tickets waiting, with everything we know about each one:

{json.dumps(evidence["tickets"], indent=2)}

Here is our written policy. These rules apply no matter what you decide.
Each rule lifts a ticket UP the queue. None of them ever pushes one down.

{json.dumps(evidence["policy"], indent=2)}

Decide the order a human should handle these in.

Reply with JSON only, no other text, in exactly this shape. Every field is
required.

{{
  "order": ["TICK-00000", "TICK-00000"],
  "reasons": {{
    "TICK-00000": "one sentence saying what decided this ticket's place"
  }},
  "the_trade_off": "two or three sentences naming what you chose to favour, what you chose to sacrifice, and what that costs us",
  "conflicts_i_noticed": [
    {{
      "tickets": ["TICK-00000"],
      "what_disagreed": "which two sources or signals pointed different ways",
      "which_i_believed": "which one you went with",
      "why": "why that source was the more reliable one here"
    }}
  ],
  "hardest_call": "which single decision was closest, and why it could reasonably have gone the other way",
  "strategy_ranking": [
    {{
      "place": 1,
      "strategy": "money, damage, deadline or fairness",
      "why_it_ranks_here": "why this one deserved the most weight for THIS batch",
      "what_it_gets_wrong": "the drawback you are accepting by weighting it highest"
    }}
  ],
  "why_the_winner_beat_the_runner_up": "one or two sentences on the closest of the four"
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": HOW_THE_AGENT_SHOULD_THINK},
            {"role": "user", "content": question},
        ],
        temperature=0.2,
        max_tokens=8000,
        response_format={"type": "json_object"},
    )

    text = response.choices[0].message.content

    if not text or not text.strip():
        raise RuntimeError(
            "The model sent back nothing. This usually means the batch was "
            "too large for one answer. Try fewer tickets, or raise max_tokens."
        )

    return json.loads(text)


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

    for ticket_id, reason in answer.get("reasons", {}).items():
        f = facts_by_id.get(ticket_id)
        if f is None:
            continue

        # Take out apostrophes, because "isn't" can be typed two ways
        # and we do not want to miss one of them.
        words = reason.lower().replace("'", "").replace("\u2019", "")

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
            "work stoppage", "work is blocked", "are blocked",
        ])
        saying_the_opposite = any(phrase in words for phrase in [
            "not blocked", "no work is blocked", "isnt blocking", "not blocking",
            "no blockage", "not block", "nothing is blocked", "work is not blocked",
        ])
        if saying_the_opposite:
            sounds_blocking = False

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
        saying_not_late = any(phrase in words for phrase in [
            "not overdue", "not yet overdue", "still remain", "remain before",
            "not late", "before the deadline", "ample time",
        ])
        if saying_not_late:
            sounds_late = False

        if sounds_late and not f["already_late"]:
            complaints.append({
                "ticket": ticket_id,
                "the_model_said": reason,
                "but_the_data_says": f"{f['hours_left']} hours still remain",
            })

    return complaints


def ask_the_model_to_fix_its_reasons(answer, complaints, evidence):
    """
    Tells the model which of its reasons the data does not support,
    and asks it to write those ones again.

    The order stays as it was. We are correcting how the decision was
    explained, not the decision itself.
    """
    tickets_to_fix = sorted({c["ticket"] for c in complaints})

    question = f"""
You gave reasons for your ordering. Some of them claim things our data does
not support:

{json.dumps(complaints, indent=2)}

Here are the tickets again so you can check the numbers:

{json.dumps(evidence["tickets"], indent=2)}

Write a new reason for these tickets only: {", ".join(tickets_to_fix)}

Do not change any other reason. Do not change the ordering.

Each new reason must still explain WHY the ticket sits where it does. Do not
simply list the numbers back. Say what about the ticket earned it that place,
using only what the data actually shows. Keep it to one sentence, the same
length as the others.

Reply with JSON only, in exactly this shape, containing only the tickets
listed above:

{{
  "reasons": {{
    "TICK-00000": "the corrected reason"
  }}
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

    fixed = json.loads(response.choices[0].message.content).get("reasons", {})

    # Only accept corrections for the tickets we asked about. If the model
    # rewrites everything, we ignore the parts we did not ask for.
    return {t: r for t, r in fixed.items() if t in tickets_to_fix}


def check_the_models_answer(answer, facts):
    """
    Verifies the model's order against the written policy.

    The model makes the judgement. This does not second-guess that judgement,
    it only checks the answer stayed inside the rules we are not willing to
    leave to a judgement.
    """
    order = answer["order"]

    checks = []

    # Did every ticket come back, exactly once?
    expected = {f["id"] for f in facts}
    returned = set(order)

    if expected != returned or len(order) != len(expected):
        checks.append({
            "problem": "the model did not return every ticket exactly once",
            "missing": sorted(expected - returned),
            "unexpected": sorted(returned - expected),
        })
        return checks

    # Does the order break any of our written rules?
    for b in brain.check_against_policy(order, facts):
        checks.append({
            "problem": "the order breaks our written policy",
            "ticket": b["ticket"],
            "should_move_to": b["move_to"],
            "why": b["why"],
        })

    return checks


def what_the_model_left_out(answer):
    """
    Notes any part of the required answer the model did not send back.

    A missing field is not a crash, but it is worth recording. If the
    reasoning fields keep going missing, that is a prompt problem and
    somebody should know about it.
    """
    wanted = [
        "order", "reasons", "the_trade_off", "conflicts_i_noticed",
        "hardest_call", "strategy_ranking", "why_the_winner_beat_the_runner_up",
    ]
    return [name for name in wanted if not answer.get(name)]


def run_the_agent():
    """
    The whole job, start to finish. Returns everything that happened,
    so it can be printed, saved, or sent back over the web.
    """
    batch = brain.load_batch()
    evidence = brain.gather_evidence(batch)
    facts = [brain.read_facts(item) for item in batch]

    # How solid is the scoring on its own? Worked out before we ask the AI,
    # and deliberately not shown to it. If the AI knew which decisions look
    # solid, it would start aiming for that instead of aiming to be right.
    how_solid = stability.how_solid_is_this(facts)
    orders = brain.rank_all_four_ways(facts)

    answer = ask_the_model(evidence)

    missing = what_the_model_left_out(answer)

    first_reasons = dict(answer.get("reasons", {}))
    wrong_claims = check_the_reasons_match_the_facts(answer, facts)

    corrections = {}
    still_wrong = []

    if wrong_claims:
        corrections = ask_the_model_to_fix_its_reasons(answer, wrong_claims, evidence)

        for ticket_id, new_reason in corrections.items():
            answer["reasons"][ticket_id] = new_reason

        still_wrong = check_the_reasons_match_the_facts(answer, facts)

    # We use .get with a fallback on the reasoning fields. The model very
    # occasionally drops one, and losing a paragraph of explanation should
    # not throw away a decision that is otherwise sound. What it dropped
    # is recorded in the checks instead.
    result = {
        "order": answer["order"],
        "reasons": answer.get("reasons", {}),
        "the_trade_off": answer.get("the_trade_off", ""),
        "hardest_call": answer.get("hardest_call", ""),
        "conflicts_i_noticed": answer.get("conflicts_i_noticed", []),
        "strategy_ranking": answer.get("strategy_ranking", []),
        "why_the_winner_beat_the_runner_up": answer.get(
            "why_the_winner_beat_the_runner_up", ""),
        "checks": {
            "policy": check_the_models_answer(answer, facts),
            "reasons_the_data_did_not_support": wrong_claims,
            "reasons_we_asked_the_model_to_rewrite": corrections,
            "still_unsupported_after_rewriting": still_wrong,
            "parts_of_the_answer_the_model_left_out": missing,
            "needs_a_human_to_look": bool(still_wrong) or bool(missing),
        },
        "reasons_before_correction": first_reasons,
        "how_solid_the_scoring_is": how_solid["by_ticket"],
    }

    # Keep a record of this decision, so somebody can ask later why
    # a complaint was placed where it was.
    record = decision_log.build_the_record(result, facts, orders)
    result["saved_to"] = decision_log.save_the_record(record)
    result["decision_id"] = record["decision_id"]

    # Also write the same story out in a Word file, so anybody can read
    # what the agent did without having to open the code.
    result["written_up_in"] = thinking_log.write_this_run(result, facts, orders)
    result["also_written_up_in"] = thinking_log.write_this_run_as_markdown(
        result, facts, orders)

    return result


def print_the_result(result):
    """Shows the result on screen in a way a person can read."""

    print("\nORDER THE AGENT CHOSE")
    print("-" * 60)
    for position, ticket_id in enumerate(result["order"], start=1):
        print(f"  {position}. {ticket_id}")
        print(f"     {result['reasons'].get(ticket_id, 'no reason given')}")

    print("\nTHE TRADE-OFF")
    print("-" * 60)
    print(f"  {result['the_trade_off'] or 'the model did not send this back'}")

    print("\nHARDEST CALL")
    print("-" * 60)
    print(f"  {result['hardest_call'] or 'the model did not send this back'}")

    print("\nCONFLICTS THE AGENT NOTICED")
    print("-" * 60)
    if not result["conflicts_i_noticed"]:
        print("  The model did not send this back.")
    else:
        for c in result["conflicts_i_noticed"]:
            print(f"\n  {', '.join(c.get('tickets', []))}")
            print(f"     what disagreed: {c.get('what_disagreed', '')}")
            print(f"     it believed:    {c.get('which_i_believed', '')}")
            print(f"     why:            {c.get('why', '')}")

    print("\nHOW IT RANKED THE FOUR WAYS OF DECIDING")
    print("-" * 60)
    if not result["strategy_ranking"]:
        print("  The model did not send this back.")
    else:
        for st in result["strategy_ranking"]:
            print(f"\n  {st.get('place', '?')}. {st.get('strategy', '')}")
            print(f"     why here:   {st.get('why_it_ranks_here', '')}")
            print(f"     gets wrong: {st.get('what_it_gets_wrong', '')}")

        if result["why_the_winner_beat_the_runner_up"]:
            print("\n  Closest call between the four:")
            print(f"  {result['why_the_winner_beat_the_runner_up']}")

    checks = result["checks"]

    print("\nDO THE REASONS MATCH OUR DATA?")
    print("-" * 60)

    if not checks["reasons_the_data_did_not_support"]:
        print("  Every reason is supported by the numbers we hold.")
    else:
        for c in checks["reasons_the_data_did_not_support"]:
            print(f"  {c['ticket']}")
            print(f"    it said:           {c['the_model_said']}")
            print(f"    but the data says: {c['but_the_data_says']}")

        print("\n  Asked the model to write those reasons again.")

        for ticket_id, new_reason in checks["reasons_we_asked_the_model_to_rewrite"].items():
            print(f"\n  {ticket_id} now reads:")
            print(f"    {new_reason}")

        if checks["still_unsupported_after_rewriting"]:
            print("\n  Some reasons still do not match the data.")
        else:
            print("\n  All reasons now match the data.")

    print("\nDOES THE ORDER FOLLOW OUR POLICY?")
    print("-" * 60)

    if not checks["policy"]:
        print("  Every ticket came back once and no rule was broken.")
    else:
        for p in checks["policy"]:
            print(f"  {p['problem']}")
            for key, value in p.items():
                if key != "problem":
                    print(f"    {key}: {value}")

    if checks["parts_of_the_answer_the_model_left_out"]:
        print("\n  The model left these parts out of its answer:")
        for name in checks["parts_of_the_answer_the_model_left_out"]:
            print(f"    {name}")

    print("\nHOW SOLID WAS THE SCORING UNDERNEATH?")
    print("-" * 60)
    print("  We changed one number at a time and re-ran the four ways of")
    print("  ranking, to see which decisions were close calls.")
    print("  This measures the scoring, not the AI's final answer.\n")

    for r in result["how_solid_the_scoring_is"].values():
        print(f"  {r['id']}  {r['how_solid']}  "
              f"({r['small_changes_that_move_it']} of {r['small_changes_tried']} "
              f"small changes move it)")

        for m in r["what_would_move_it"][:2]:
            print(f"    if {m['if']}, it moves from {m['moves_from']} to {m['moves_to']}")

    print("\nROUTING")
    print("-" * 60)

    for position, ticket_id in enumerate(result["order"], start=1):
        when = "now" if position == 1 else ("next" if position <= 3 else "queued")

        solid = result["how_solid_the_scoring_is"].get(ticket_id)
        note = ""
        if solid and solid["worth_a_second_look"]:
            note = "   <- the scoring was not settled about this one"

        print(f"  ROUTE {ticket_id} -> HUMAN AGENT  ({when}){note}")

    if checks["needs_a_human_to_look"]:
        print("\n  This whole decision is flagged for human review before it")
        print("  is acted on, because part of the answer could not be verified.")

    if result.get("saved_to"):
        print("\nSAVED")
        print("-" * 60)
        print(f"  This decision is on record as {result['decision_id']}")
        print(f"  Written to {result['saved_to']}")
        print("  Anyone can open that file later and see exactly what the")
        print("  agent knew, what it chose, and why.")


if __name__ == "__main__":
    print("\nAsking the agent to decide...")
    print_the_result(run_the_agent())
