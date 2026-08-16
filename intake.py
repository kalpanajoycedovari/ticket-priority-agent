"""
intake.py

Turns what a customer actually wrote into a ticket the agent can work with.

Somebody types "my export has stopped working and I need it for a meeting".
That is not a ticket yet. It has no problem type, no customer attached, and
no reading from monitoring or the contract clock.

This file does the first half: read the words, work out what kind of problem
it is and how serious the customer thinks it is. The second half, looking up
the three systems, happens in the code that follows.
"""

import os
import json

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"

# The same seventeen kinds of problem the rest of the project uses.
# The model must pick one of these and nothing else, so that everything
# downstream keeps working.
KINDS_OF_PROBLEM = [
    "system_outage", "security_incident", "data_loss", "compliance_request",
    "payment_failure", "login_failure", "data_export_failure",
    "account_lockout", "api_failure", "billing_error", "slow_performance",
    "integration_failure", "notification_failure", "dashboard_bug",
    "feature_request", "how_to_question", "password_reset",
]

SEVERITY_WORDS = ["Low", "Medium", "High", "Critical"]


print("Intake loaded.")
HOW_TO_READ_A_COMPLAINT = """
You work on the intake desk of a customer support team. Somebody has written
in. Your only job is to turn their words into a tidy ticket. You do not decide
how urgent it is and you do not decide who gets helped first. Somebody else
does that.

Two things to be careful about.

First, work out what KIND of problem this is from what they describe, not from
the words they reach for. Somebody saying "urgent" does not make it an outage.
Somebody saying "quick question" about their files disappearing does not make
it a how-to question.

Second, record how serious THEY think it is, separately from anything else.
That is their opinion and it is often wrong, but it is worth keeping, because
the gap between what they claim and what our systems measure is useful later.

If you genuinely cannot tell what kind of problem it is, say so rather than
guessing. A wrong label is worse than an honest 'not sure'.
"""


def read_a_complaint(what_they_wrote):
    """
    Takes plain writing and turns it into the parts of a ticket that can
    only come from the person: what kind of problem, how serious they think
    it is, and a short subject line.

    Everything else about the ticket comes from our own systems, not from
    what they typed.
    """
    question = f"""
Here is what the customer wrote:

"{what_they_wrote}"

Turn it into a ticket.

Pick the kind of problem from exactly this list, nothing else:
{", ".join(KINDS_OF_PROBLEM)}

Reply with JSON only, in exactly this shape:

{{
  "issue_type": "one of the kinds listed above",
  "subject": "a short subject line, under eight words",
  "reported_severity": "Low, Medium, High or Critical, meaning how serious THEY think it is",
  "sure_about_the_kind": true,
  "what_made_me_pick_it": "the words in their message that decided the kind of problem",
  "anything_worrying": "anything a human should see straight away, or an empty string"
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": HOW_TO_READ_A_COMPLAINT},
            {"role": "user", "content": question},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)
import csv
import random
from datetime import datetime

DATA_FOLDER = "data"


def load(filename):
    with open(os.path.join(DATA_FOLDER, filename), "r",
              newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def look_up_the_customer(customer_id):
    """Finds one customer in our records."""
    for row in load("customers.csv"):
        if row["customer_id"] == customer_id:
            return row
    return None


def list_some_customers(how_many=8):
    """A few real customers to choose from, so you can pick who is writing in."""
    everyone = load("customers.csv")
    picked = random.sample(everyone, min(how_many, len(everyone)))
    return sorted(picked, key=lambda c: -int(c["monthly_value_gbp"]))
def what_monitoring_would_see(kind_of_problem):
    """
    Stands in for the monitoring system.

    In a real company this would be a call to Datadog or similar. Here it
    produces a believable reading for this kind of problem, using the same
    rules the practice data was built with, including the blind spot.
    """
    blind_to = ["security_incident", "compliance_request", "billing_error"]
    only_one_person = ["password_reset", "how_to_question", "feature_request"]
    usually_blocking = ["system_outage", "payment_failure", "account_lockout",
                        "api_failure", "data_loss"]
    sometimes_blocking = ["login_failure", "integration_failure",
                          "data_export_failure"]

    if kind_of_problem in blind_to:
        severity = "Low"
        affected = random.randint(1, 3)
        blocked = False
    elif kind_of_problem in only_one_person:
        severity = "Low"
        affected = 1
        blocked = False
    elif kind_of_problem in usually_blocking:
        severity = random.choice(["High", "Critical"])
        affected = random.randint(50, 3000)
        blocked = random.random() < 0.8
    elif kind_of_problem in sometimes_blocking:
        severity = random.choice(["Medium", "High"])
        affected = random.randint(5, 200)
        blocked = random.random() < 0.4
    else:
        severity = random.choice(["Low", "Medium"])
        affected = random.randint(1, 40)
        blocked = False

    return {
        "ticket_id": "",
        "service_name": random.choice([
            "auth-service", "billing-api", "export-worker",
            "web-app", "notify-service", "sync-engine"]),
        "affected_users": str(affected),
        "error_rate_percent": str(round(random.uniform(0, 8) if severity == "Low"
                                        else random.uniform(5, 95), 1)),
        "system_load_percent": str(random.randint(20, 99)),
        "work_is_blocked": str(blocked),
        "observed_severity": severity,
    }


def what_the_clock_says(customer, hours_since_it_arrived=None):
    """
    Stands in for the contract clock.

    How long we promised depends on the plan. How much time is left depends
    on how long the complaint has been sitting there.
    """
    promised = float(customer["promised_response_hours"])

    if hours_since_it_arrived is None:
        hours_since_it_arrived = round(random.uniform(0.2, promised * 1.6), 1)

    left = round(promised - hours_since_it_arrived, 1)

    return {
        "ticket_id": "",
        "customer_id": customer["customer_id"],
        "promised_response_hours": str(promised),
        "first_reply_hours": str(hours_since_it_arrived),
        "hours_left_before_promise_broken": str(left),
        "promise_was_broken": str(left < 0),
    }
def make_a_full_ticket(what_they_wrote, customer_id, ticket_number,
                       times_they_have_asked=1):
    """
    Takes plain writing and builds a complete ticket, ready for the agent.

    The customer's own words give us the kind of problem and the severity
    they claim. Everything else comes from our own systems, because that is
    where it comes from in real life. Nobody types in how many users are
    affected.
    """
    read = read_a_complaint(what_they_wrote)

    customer = look_up_the_customer(customer_id)
    if customer is None:
        raise ValueError(f"No customer with id {customer_id}")

    monitoring = what_monitoring_would_see(read["issue_type"])
    clock = what_the_clock_says(customer)

    return {
        "ticket": {
            "ticket_id": f"NEW-{ticket_number:05d}",
            "customer_id": customer_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "issue_type": read["issue_type"],
            "subject": read["subject"],
            "message": what_they_wrote,
            "reported_severity": read["reported_severity"],
            "customer_mood": "unknown",
            "times_contacted_about_this": str(times_they_have_asked),
        },
        "customer": customer,
        "telemetry": monitoring,
        "sla": clock,
        "how_it_was_read": read,
    }
def build_a_batch(inbox, save_as="new_batch.json"):
    """
    Turns a list of written complaints into a batch file the agent can read.

    Each one gets a customer attached and a reading from monitoring and the
    clock, because those come from our systems rather than from the person
    writing in.
    """
    customers = list_some_customers(len(inbox))

    batch = []

    for i, entry in enumerate(inbox, start=1):
        if isinstance(entry, dict):
            words = entry["words"]
            customer_id = entry.get("customer_id") or customers[i - 1]["customer_id"]
            asked = entry.get("times_asked", 1)
        else:
            words = entry
            customer_id = customers[i - 1]["customer_id"]
            asked = 1

        ticket = make_a_full_ticket(words, customer_id, i, asked)

        ticket["telemetry"]["ticket_id"] = ticket["ticket"]["ticket_id"]
        ticket["sla"]["ticket_id"] = ticket["ticket"]["ticket_id"]

        batch.append(ticket)
        print(f"  read {ticket['ticket']['ticket_id']}  "
              f"{ticket['ticket']['issue_type']}")

    path = os.path.join(DATA_FOLDER, save_as)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(batch, f, indent=2)

    print(f"\nSaved {len(batch)} tickets to {path}")
    return path
if __name__ == "__main__":
    # Ten complaints written the way people actually write them, chosen so
    # that no obvious order exists. Several are genuinely urgent at the same
    # time, and several sound urgent but are not.
    #
    # Where a customer is named, it is chosen on purpose: the break-in belongs
    # to somebody tiny, the shouting belongs to somebody expensive.
    inbox = [
        "our whole team is locked out. nobody can get in since about 6am. we "
        "have a client demo at 10 and I don't know what to tell them",

        "I need to flag something. one of our customers has asked us to delete "
        "everything we hold on them. I believe there's a legal time limit on "
        "this and we're already a few days in",

        "payments are failing at checkout. we've had maybe forty customers "
        "email us this morning saying their card was declined. our own test "
        "card fails too",

        "there is a session logged in from a device we don't recognise and I "
        "can't work out how to end it. probably nothing but thought I should "
        "mention it",

        "ABSOLUTELY UNACCEPTABLE. our dashboard chart is showing last month's "
        "figures. we pay you thousands every month and I expect better than "
        "this. I want someone to call me today",

    ]

    print(f"\nReading {len(inbox)} complaints as they were written...\n")
    build_a_batch(inbox)
    print("\nNow run:  python decide_new.py")