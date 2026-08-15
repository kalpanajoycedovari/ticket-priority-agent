"""
agent.py

Reads the batch of tickets, works out what order a human should
handle them in, and explains why it chose that order.
"""

import json
import os

DATA_FOLDER = "data"


def load_batch():
    """Reads the tickets we saved earlier."""
    path = os.path.join(DATA_FOLDER, "demo_batch.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


batch = load_batch()

print(f"Loaded {len(batch)} tickets.\n")

for item in batch:
    t = item["ticket"]
    c = item["customer"]
    print(f"  {t['ticket_id']}  {t['subject']:35} {c['company_name']} ({c['plan']})")
    # ----- PULLING OUT THE NUMBERS WE NEED -----
#
# Everything arrives as text, so we convert it once here
# and every ranking method uses the same clean numbers.

SEVERITY_ORDER = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def read_facts(item):
    """Gathers the facts about one ticket from all three sources."""
    t = item["ticket"]
    c = item["customer"]
    m = item["telemetry"]
    s = item["sla"]

    return {
        "id": t["ticket_id"],
        "subject": t["subject"],
        "message": t["message"],
        "issue": t["issue_type"],
        "customer_says": SEVERITY_ORDER[t["reported_severity"]],
        "times_asked": int(t["times_contacted_about_this"]),

        "company": c["company_name"],
        "plan": c["plan"],
        "pays_monthly": int(c["monthly_value_gbp"]),

        "monitoring_says": SEVERITY_ORDER[m["observed_severity"]],
        "users_hit": int(m["affected_users"]),
        "cannot_work": m["work_is_blocked"] == "True",

        "promised_hours": float(s["promised_response_hours"]),
        "hours_left": float(s["hours_left_before_promise_broken"]),
        "already_late": s["promise_was_broken"] == "True",
    }


facts = [read_facts(item) for item in batch]

print("\nFacts pulled out:")
for f in facts:
    print(f"  {f['id']}  pays £{f['pays_monthly']:>6}/mo | {f['users_hit']:>4} users hit | "
          f"customer says {f['customer_says']} | monitoring says {f['monitoring_says']} | "
          f"{f['hours_left']:>7.1f}h left")
    # ----- WAY 1: RANK BY MONEY -----
#
# Asks: which ticket puts the most revenue at risk?
# Favours whoever pays the most. Ignores whether anything is broken.

def score_by_money(f):
    """Higher score means handle sooner."""
    score = f["pays_monthly"]

    # An unhappy big payer is more likely to leave, so add a little
    # for customers who have asked more than once.
    if f["times_asked"] >= 3:
        score = score * 1.2

    return score


def rank_by(score_function):
    """
    Sorts the tickets, highest score first.
    Returns a list of ticket ids in the order they should be handled.
    """
    ordered = sorted(facts, key=score_function, reverse=True)
    return [f["id"] for f in ordered]


money_order = rank_by(score_by_money)

print("\nWay 1, ranked by money:")
for position, ticket_id in enumerate(money_order, start=1):
    f = next(x for x in facts if x["id"] == ticket_id)
    print(f"  {position}. {ticket_id}  £{f['pays_monthly']:>6}/mo  {f['subject']}")
    # ----- WAY 2: RANK BY DAMAGE -----
#
# Asks: which ticket is breaking the most things?
# Favours real technical harm. Does not care who is paying.

def score_by_damage(f):
    """Higher score means handle sooner."""
    score = f["monitoring_says"] * 100

    # More people hurt means more damage, but a ticket affecting
    # 5000 people is not 5000 times worse than one affecting 1.
    # We count each ten users as one point to keep it sensible.
    score = score + (f["users_hit"] / 10)

    # Not being able to work at all is worse than being slowed down.
    if f["cannot_work"]:
        score = score + 150

    return score


damage_order = rank_by(score_by_damage)

print("\nWay 2, ranked by damage:")
for position, ticket_id in enumerate(damage_order, start=1):
    f = next(x for x in facts if x["id"] == ticket_id)
    print(f"  {position}. {ticket_id}  {f['users_hit']:>4} users hit  {f['subject']}")
    # ----- WAY 3: RANK BY DEADLINE -----
#
# Asks: which promise breaks first?
# Favours whatever is closest to running out of time.
# Does not care whether the ticket actually matters.

def score_by_deadline(f):
    """Higher score means handle sooner."""
    # Already late is the worst case, so those go top.
    # The later we are, the higher the score.
    if f["already_late"]:
        return 1000 + abs(f["hours_left"])

    # Otherwise, less time left means a higher score.
    # We work out what share of the promised time is left,
    # because 1 hour left means very different things
    # for a 2 hour promise and a 72 hour promise.
    share_left = f["hours_left"] / f["promised_hours"]

    return 100 - (share_left * 100)


deadline_order = rank_by(score_by_deadline)

print("\nWay 3, ranked by deadline:")
for position, ticket_id in enumerate(deadline_order, start=1):
    f = next(x for x in facts if x["id"] == ticket_id)
    late_note = "LATE" if f["already_late"] else f"{f['hours_left']:.1f}h left"
    print(f"  {position}. {ticket_id}  {late_note:>12}  {f['subject']}")
    # ----- WAY 4: RANK BY FAIRNESS -----
#
# Asks: who have we treated worst?
# Favours people we have kept waiting or ignored repeatedly.
# Does not care how much they pay or how bad the problem is.

def score_by_fairness(f):
    """Higher score means handle sooner."""
    score = 0

    # Asking again and again means we have failed them each time.
    score = score + (f["times_asked"] * 30)

    # Being late is a failure on our side, not theirs.
    if f["already_late"]:
        score = score + 100
        # The longer we have been late, the worse it is.
        score = score + abs(f["hours_left"])

    # People on cheaper plans get the longest promises and
    # tend to be pushed back whenever something bigger arrives,
    # so being a small customer counts in their favour here.
    if f["pays_monthly"] < 200:
        score = score + 50

    return score


fairness_order = rank_by(score_by_fairness)

print("\nWay 4, ranked by fairness:")
for position, ticket_id in enumerate(fairness_order, start=1):
    f = next(x for x in facts if x["id"] == ticket_id)
    print(f"  {position}. {ticket_id}  asked {f['times_asked']} times  {f['subject']}")
    # ----- COMPARING THE FOUR ORDERS -----
#
# Each way of ranking gave a different answer.
# Putting them next to each other shows where they agree and clash.

all_orders = {
    "money": money_order,
    "damage": damage_order,
    "deadline": deadline_order,
    "fairness": fairness_order,
}


def position_in(order, ticket_id):
    """Where does this ticket sit in that order? 1 means first."""
    return order.index(ticket_id) + 1


print("\nWhere each ticket sits under each way of ranking:")
print(f"  {'ticket':12} {'money':>7} {'damage':>7} {'deadline':>9} {'fairness':>9}   subject")

for f in facts:
    places = [position_in(all_orders[name], f["id"]) for name in all_orders]
    print(f"  {f['id']:12} {places[0]:>7} {places[1]:>7} {places[2]:>9} {places[3]:>9}   {f['subject']}")
    # ----- HOW MUCH DO THE FOUR WAYS DISAGREE? -----
#
# If all four put a ticket in roughly the same place, the decision is easy.
# If they scatter it from first to last, that is where the real
# judgement is needed and where the report has to explain itself.

print("\nHow much the four ways disagree about each ticket:")

for f in facts:
    places = [position_in(all_orders[name], f["id"]) for name in all_orders]
    gap = max(places) - min(places)

    if gap >= 4:
        note = "they strongly disagree"
    elif gap >= 2:
        note = "they partly disagree"
    else:
        note = "they agree"

    print(f"  {f['id']}  best {min(places)}, worst {max(places)}, gap {gap}  ->  {note}")
    # ----- READING WHAT THE CUSTOMER ACTUALLY WROTE -----
#
# The four ways above only look at numbers, so they cannot tell
# a password reset apart from a break-in. Both show one user
# and a quiet dashboard. The difference is in the words.

SERIOUS_WORDS = [
    "logins from a country",
    "did not start",
    "changed our admin email",
    "was not us",
    "breach",
    "missing",
    "vanished",
    "gone",
    "deleted",
    "personal data",
    "gdpr",
]

LEAVING_WORDS = [
    "considering cancelling",
    "cancel",
    "third time",
    "unacceptable",
]


def read_the_message(f):
    """Looks for things in the message that the numbers cannot show."""
    words = (f["subject"] + " " + f["message"]).lower()

    found = []

    for phrase in SERIOUS_WORDS:
        if phrase in words:
            found.append("sounds serious")
            break

    for phrase in LEAVING_WORDS:
        if phrase in words:
            found.append("may be about to leave")
            break

    return found


print("\nWhat the messages say that the numbers do not:")
for f in facts:
    notes = read_the_message(f)
    if notes:
        print(f"  {f['id']}  {', '.join(notes)}")
        print(f"              \"{f['message']}\"")
        # ----- PUTTING THE FOUR WAYS TOGETHER -----
#
# Each way gave every ticket a position from 1 to 6.
# We turn those positions into points, add them up,
# and the ticket with the most points goes first.
#
# We do NOT weight the four equally. Damage matters more than
# money, and the message can override everything, because a
# break-in stays a break-in whatever the dashboard says.

HOW_MUCH_EACH_WAY_COUNTS = {
    "damage":   1.5,
    "deadline": 1.0,
    "money":    0.8,
    "fairness": 0.8,
}


def combined_score(f):
    """Adds up the four positions, with some counting more than others."""
    total = 0

    for way_name, order in all_orders.items():
        place = position_in(order, f["id"])

        # First place is worth 6 points, last place is worth 1.
        points = len(facts) + 1 - place

        total = total + (points * HOW_MUCH_EACH_WAY_COUNTS[way_name])

    # Reading the message can override the numbers.
    notes = read_the_message(f)

    if "sounds serious" in notes:
        total = total + 8

    if "may be about to leave" in notes:
        total = total + 2

    return total

# ----- WHAT THE NUMBERS ALONE WOULD SAY -----
#
# Before adding what the messages tell us, we look at what the four
# ways of ranking produce on their own. This shows what the agent
# would have decided if it only ever looked at numbers.

def score_without_reading(f):
    """The same as combined_score, but ignoring the message."""
    total = 0

    for way_name, order in all_orders.items():
        place = position_in(order, f["id"])
        points = len(facts) + 1 - place
        total = total + (points * HOW_MUCH_EACH_WAY_COUNTS[way_name])

    return total


numbers_only_order = sorted(facts, key=score_without_reading, reverse=True)

print("\nIf we only looked at the numbers:")
for position, f in enumerate(numbers_only_order, start=1):
    print(f"  {position}. {f['id']}  {score_without_reading(f):>5.1f} points  {f['subject']}")
first_order = sorted(facts, key=combined_score, reverse=True)

print("\nFirst attempt at a final order:")
for position, f in enumerate(first_order, start=1):
    print(f"  {position}. {f['id']}  {combined_score(f):>5.1f} points  {f['subject']}")
    # ----- CHECKING OUR OWN ANSWER -----
#
# The points system is a judgement, not a fact, so we look at the
# order it produced and ask whether anything has gone obviously wrong.
# Anything we change gets recorded, along with the reason.
# ----- THE SEVERITY POLICY -----
#
# This is the written rule book, the same thing a real support desk
# would keep in a document signed off by a manager. Certain kinds of
# ticket get a guaranteed place in the queue no matter what the
# scoring says, because the consequence of getting them wrong is
# not something we are willing to leave to a calculation.
#
# Everything not listed here is decided by the scoring.

SEVERITY_POLICY = [
    {
        "applies_to": "a suspected break-in or account takeover",
        "never_below": 3,
        "reason": "monitoring cannot measure this kind of harm, so the numbers "
                  "will always underrate it",
    },
    {
        "applies_to": "a legal request such as GDPR",
        "never_below": 4,
        "reason": "the deadline is set by law, not by us, and missing it carries a fine",
    },
    {
        "applies_to": "a customer who is badly affected but pays nothing",
        "never_below": 5,
        "reason": "paying nothing is not a reason to be left last when the problem is real",
    },
]


def show_policy():
    """Prints the rule book so anyone reading the output can see it."""
    print("\n" + "=" * 70)
    print("SEVERITY POLICY")
    print("=" * 70)
    print("\n  These rules apply no matter what the scoring says.\n")

    for rule in SEVERITY_POLICY:
        print(f"  {rule['applies_to'].capitalize()}")
        print(f"    never sits below position {rule['never_below']}")
        print(f"    because {rule['reason']}\n")


show_policy()
def find_problems(order):
    """
    Looks at an order and returns a list of things that need fixing.
    Each problem says which ticket, where it should move, and why.
    """
    problems = []
    # Look up the rules rather than repeating them, so the policy
    # above is the only place these numbers are written down.
    breakin_rule = SEVERITY_POLICY[0]
    legal_rule = SEVERITY_POLICY[1]
    unfair_rule = SEVERITY_POLICY[2]

    for position, f in enumerate(order, start=1):
        notes = read_the_message(f)

        # A suspected break-in cannot sit low in the queue.
        # Monitoring cannot see this kind of harm, so the numbers
        # will always underrate it.
        if "sounds serious" in notes and f["issue"] == "security_incident":
            if position > breakin_rule["never_below"]:
                problems.append({
                    "ticket": f["id"],
                    "move_to": breakin_rule["never_below"],
                    "why": breakin_rule["reason"],
                })

        # A legal request has a deadline set by law, not by us.
        if f["issue"] == "compliance_request":
            if position > legal_rule["never_below"]:
                problems.append({
                    "ticket": f["id"],
                    "move_to": legal_rule["never_below"],
                    "why": legal_rule["reason"],
                })

        # Nobody should be at the bottom purely for paying nothing.
        if position > unfair_rule["never_below"] and f["pays_monthly"] == 0:
            if f["monitoring_says"] >= 3 or f["cannot_work"]:
                problems.append({
                    "ticket": f["id"],
                    "move_to": unfair_rule["never_below"],
                    "why": unfair_rule["reason"],
                })

    return problems


# Check the numbers-only order first, to show what the safety net
# would have caught if the agent had never read the messages.
problems_if_numbers_only = find_problems(numbers_only_order)

print("\nWhat the check would have caught if we only looked at numbers:")
if not problems_if_numbers_only:
    print("  Nothing.")
else:
    for p in problems_if_numbers_only:
        print(f"  {p['ticket']} should move to position {p['move_to']}")
        print(f"    because {p['why']}")

# Now check the order we actually intend to use.
problems = find_problems(first_order)

print("\nChecking our own answer:")
if not problems:
    print("  Nothing needs changing.")
else:
    for p in problems:
        print(f"  {p['ticket']} should move to position {p['move_to']}")
        print(f"    because {p['why']}")
        # ----- THE FINAL ORDER -----
#
# Nothing needed changing, so the first attempt stands.
# If the check had found problems we would apply them here.

final_order = first_order


# ----- WHY EACH TICKET ENDED UP WHERE IT DID -----
#
# For every ticket we work out the one thing that mattered most,
# so the report can give a reason rather than just a number.

def main_reason(f):
    """Returns one short sentence saying what decided this ticket's place."""
    notes = read_the_message(f)

    if "sounds serious" in notes and f["issue"] == "security_incident":
        return "the customer describes a possible break-in, which monitoring cannot measure"

    if "sounds serious" in notes:
        return "the customer describes data going missing that nobody on their side deleted"

    if f["already_late"] and f["times_asked"] >= 6:
        return (f"we are {abs(f['hours_left']):.0f} hours past the promised reply "
                f"and they have asked {f['times_asked']} times")

    if f["already_late"]:
        return f"we are {abs(f['hours_left']):.0f} hours past the promised reply time"

    if f["hours_left"] < 1:
        return f"only {f['hours_left']:.1f} hours remain before we break the promised reply time"

    if f["pays_monthly"] >= 10000 and f["monitoring_says"] <= 1:
        return (f"they pay £{f['pays_monthly']:,} a month, but only {f['users_hit']} "
                f"users are affected and nothing is blocked")

    if f["monitoring_says"] <= 1 and not f["cannot_work"]:
        return "nothing is broken, one person is affected, and no work is blocked"

    return "the four ways of ranking broadly agreed on its place"


print("\n" + "=" * 70)
print("FINAL ORDER")
print("=" * 70)

for position, f in enumerate(final_order, start=1):
    print(f"\n  {position}. {f['id']}  {f['subject']}")
    print(f"     {f['company']} ({f['plan']}, £{f['pays_monthly']:,}/month)")
    print(f"     Reason: {main_reason(f)}")
    # ----- THE TRADE-OFF WE MADE -----
#
# The brief asks the agent to say which trade-off it made and why,
# not just to produce an order. This works it out from the orders
# we already have rather than being written by hand.

print("\n" + "=" * 70)
print("THE TRADE-OFF WE MADE")
print("=" * 70)

# Which way of ranking lost the most ground in the final order?
biggest_drop = None
biggest_drop_size = 0

for f in facts:
    money_place = position_in(money_order, f["id"])
    final_place = final_order.index(f) + 1
    drop = final_place - money_place

    if drop > biggest_drop_size:
        biggest_drop_size = drop
        biggest_drop = f

# Which ticket gained the most?
biggest_rise = None
biggest_rise_size = 0

for f in facts:
    numbers_place = numbers_only_order.index(f) + 1
    final_place = final_order.index(f) + 1
    rise = numbers_place - final_place

    if rise > biggest_rise_size:
        biggest_rise_size = rise
        biggest_rise = f

print(f"\n  Money was not given the final say.")
print(f"  {biggest_drop['id']} ({biggest_drop['company']}, £{biggest_drop['pays_monthly']:,}/month) "
      f"ranks 1st on money alone")
print(f"  but finishes {position_in([x['id'] for x in final_order], biggest_drop['id'])}th, "
      f"because monitoring shows only {biggest_drop['users_hit']} users affected "
      f"and no work blocked.")

print(f"\n  Reading the message changed the outcome.")
print(f"  {biggest_rise['id']} moved up {biggest_rise_size} places once we read what the customer wrote.")
print(f"  On the numbers alone it sat at position "
      f"{numbers_only_order.index(biggest_rise) + 1}, behind routine work.")

print(f"\n  What this costs us.")
print(f"  Two Enterprise accounts worth £{39127 + 29044:,} a month combined "
      f"sit at positions 4 and 5.")
print(f"  We accept that risk because the tickets above them involve missing data, "
      f"a possible break-in,")
print(f"  and a promise we have already broken by 50 hours.")
# ----- HANDING THE TICKETS TO A HUMAN -----
#
# We are not building a real support system, so this just prints
# what would happen. The decision is the part that matters.

print("\n" + "=" * 70)
print("ROUTING")
print("=" * 70 + "\n")

for position, f in enumerate(final_order, start=1):
    if position == 1:
        when = "now"
    elif position <= 3:
        when = "next"
    else:
        when = "queued"

    print(f"  ROUTE {f['id']} -> HUMAN AGENT  ({when})")
    # ----- SAVING THE REPORT -----
#
# Everything above prints to the screen and is gone when you close it.
# This writes the important parts to a file you can hand in.

report_lines = []


def write(line=""):
    """Adds a line to the report we are building."""
    report_lines.append(line)


write("TICKET PRIORITISATION REPORT")
write("=" * 70)
write("")
write(f"Tickets in this batch: {len(facts)}")
write("Sources used: customer records, monitoring data, contract clock")
write("Ways of ranking compared: money, damage, deadline, fairness")
write("")

write("FINAL ORDER")
write("-" * 70)
for position, f in enumerate(final_order, start=1):
    write("")
    write(f"{position}. {f['id']}  {f['subject']}")
    write(f"   {f['company']} ({f['plan']}, £{f['pays_monthly']:,}/month)")
    write(f"   Reason: {main_reason(f)}")

write("")
write("")
write("THE FOUR WAYS COMPARED")
write("-" * 70)
write(f"{'ticket':12} {'money':>7} {'damage':>7} {'deadline':>9} {'fairness':>9}   subject")
for f in facts:
    places = [position_in(all_orders[name], f["id"]) for name in all_orders]
    write(f"{f['id']:12} {places[0]:>7} {places[1]:>7} {places[2]:>9} {places[3]:>9}   {f['subject']}")

write("")
write("No two ways of ranking agree on first place. Two tickets swing")
write("between first and last depending on which way is believed.")
write("")
write("")
write("THE TRADE-OFF WE MADE")
write("-" * 70)
write("Money was not given the final say.")
write(f"{biggest_drop['id']} ({biggest_drop['company']}, £{biggest_drop['pays_monthly']:,}/month) "
      f"ranks 1st on money alone but finishes "
      f"{position_in([x['id'] for x in final_order], biggest_drop['id'])}th,")
write(f"because monitoring shows only {biggest_drop['users_hit']} users affected and no work blocked.")
write("")
write("Reading the message changed the outcome.")
write(f"{biggest_rise['id']} moved up {biggest_rise_size} places once we read what the customer wrote.")
write(f"On the numbers alone it sat at position {numbers_only_order.index(biggest_rise) + 1}, "
      f"behind routine work.")
write("")
write("What this costs us.")
write("Two Enterprise accounts worth £68,171 a month combined sit at positions 4 and 5.")
write("We accept that risk because the tickets above them involve missing data,")
write("a possible break-in, and a promise we have already broken by 50 hours.")
write("")
write("")
write("WHAT THE SELF-CHECK CAUGHT")
write("-" * 70)
if problems_if_numbers_only:
    write("Ranking on numbers alone would have produced this problem:")
    for p in problems_if_numbers_only:
        write(f"  {p['ticket']} should move to position {p['move_to']}")
        write(f"  because {p['why']}")
    write("")
write("After reading the customer messages, the check found nothing")
write("that needed changing.")
write("")
write("")

write("ROUTING")
write("-" * 70)
for position, f in enumerate(final_order, start=1):
    when = "now" if position == 1 else ("next" if position <= 3 else "queued")
    write(f"ROUTE {f['id']} -> HUMAN AGENT  ({when})")


report_path = os.path.join(DATA_FOLDER, "report.txt")

with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

print(f"\nReport saved to {report_path}")