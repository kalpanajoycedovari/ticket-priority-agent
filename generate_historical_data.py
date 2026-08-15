"""
generate_historical_data.py

Makes fake customer support history for the ticket prioritisation agent.
Writes five CSV files into a folder called "data".
"""

import os
import csv
import random
from datetime import datetime, timedelta


# ----- SETTINGS -----
# Change these numbers if you want a bigger or smaller dataset.

HOW_MANY_CUSTOMERS = 200
HOW_MANY_TICKETS = 1000
HOW_MANY_DAYS_OF_HISTORY = 180
OUTPUT_FOLDER = "data"

# A seed means "give me the same random numbers every time I run this".
# Keep it fixed while building so your data does not change under you.
random.seed(42)
# ----- LOOKUP TABLE 1: customer plans -----
# weight     = how common this plan is (lots of free users, very few enterprise)
# min_value  = lowest they pay us per month, in pounds
# max_value  = highest they pay us per month, in pounds
# sla_hours  = how many hours we promised to reply within

CUSTOMER_PLANS = {
    "Free":       {"weight": 45, "min_value": 0,    "max_value": 0,     "sla_hours": 72},
    "Basic":      {"weight": 30, "min_value": 20,   "max_value": 120,   "sla_hours": 24},
    "Pro":        {"weight": 18, "min_value": 200,  "max_value": 1500,  "sla_hours": 8},
    "Enterprise": {"weight": 7,  "min_value": 3000, "max_value": 40000, "sla_hours": 2},
}

print("Customer plans created.")
# ----- LOOKUP TABLE 2: types of problem -----
# freq = how often this problem shows up (password resets are common, outages are rare)
# sev  = how likely each severity is FOR THIS PROBLEM. The numbers add up to 1.

ISSUE_PROFILES = {
    "system_outage":        {"freq": 1,  "sev": {"High": 0.2, "Critical": 0.8}},
    "security_incident":    {"freq": 2,  "sev": {"Medium": 0.2, "High": 0.4, "Critical": 0.4}},
    "data_loss":            {"freq": 2,  "sev": {"Medium": 0.2, "High": 0.4, "Critical": 0.4}},
    "compliance_request":   {"freq": 3,  "sev": {"Low": 0.2, "Medium": 0.5, "High": 0.3}},
    "payment_failure":      {"freq": 8,  "sev": {"Medium": 0.3, "High": 0.5, "Critical": 0.2}},
    "login_failure":        {"freq": 8,  "sev": {"Low": 0.2, "Medium": 0.5, "High": 0.3}},
    "data_export_failure":  {"freq": 5,  "sev": {"Low": 0.2, "Medium": 0.5, "High": 0.3}},
    "account_lockout":      {"freq": 8,  "sev": {"Low": 0.3, "Medium": 0.5, "High": 0.2}},
    "api_failure":          {"freq": 5,  "sev": {"Medium": 0.3, "High": 0.5, "Critical": 0.2}},
    "billing_error":        {"freq": 7,  "sev": {"Low": 0.3, "Medium": 0.5, "High": 0.2}},
    "slow_performance":     {"freq": 15, "sev": {"Low": 0.5, "Medium": 0.35, "High": 0.15}},
    "integration_failure":  {"freq": 5,  "sev": {"Medium": 0.3, "High": 0.5, "Critical": 0.2}},
    "notification_failure": {"freq": 8,  "sev": {"Low": 0.6, "Medium": 0.4}},
    "dashboard_bug":        {"freq": 10, "sev": {"Low": 0.7, "Medium": 0.3}},
    "feature_request":      {"freq": 8,  "sev": {"Low": 1.0}},
    "how_to_question":      {"freq": 10, "sev": {"Low": 1.0}},
    "password_reset":       {"freq": 15, "sev": {"Low": 0.8, "Medium": 0.2}},
}

print("Issue profiles created.")
# ----- LOOKUP TABLE 3: what the customer actually writes -----
# Each problem type holds a LIST of wordings.
# Each wording is a pair: (subject line, middle sentence).
# We pick one at random, then add an opening and closing line based on mood.

TICKET_WORDING = {
    "system_outage": [
        ("Everything is down", "None of us can reach the platform at all."),
        ("Total outage", "The site has been returning an error page for the last forty minutes."),
        ("Platform unreachable", "Every one of our staff is getting a timeout when they try to load it."),
    ],
    "security_incident": [
        ("Suspicious activity on our account", "There are logins from a country none of our staff are in."),
        ("Possible breach", "Someone has changed our admin email address and it was not us."),
        ("Unrecognised device on our account", "We can see a session we did not start and cannot end it."),
    ],
    "data_loss": [
        ("Our records have disappeared", "About three weeks of entries are missing from our workspace."),
        ("Missing data after sync", "Half our project list vanished after the sync ran last night."),
        ("Deleted records we did not delete", "A folder of client files is gone and nobody on our side removed it."),
    ],
    "compliance_request": [
        ("Data deletion request", "We need a customer's personal data removed under GDPR."),
        ("Subject access request", "A customer has asked for a copy of everything you hold on them."),
        ("Retention policy question", "We need written confirmation of how long you keep our deleted records."),
    ],
    "payment_failure": [
        ("Payments are not going through", "Card charges keep failing at the final step."),
        ("Checkout is broken", "Our customers reach the payment page and then get an error."),
        ("Card declined for everyone", "Every transaction today has been rejected, including test cards."),
    ],
    "login_failure": [
        ("Cannot sign in", "The login page rejects our details even after a reset."),
        ("Sign in loop", "It accepts my password then sends me straight back to the login screen."),
        ("Team cannot log in", "Four of my colleagues are getting an invalid credentials message."),
    ],
    "data_export_failure": [
        ("Export is broken", "The CSV download stops halfway and the file is unusable."),
        ("Cannot download report", "The export button spins for a while and then nothing happens."),
        ("Corrupted export file", "The file downloads but will not open in Excel."),
    ],
    "account_lockout": [
        ("Locked out of our account", "We have been shut out and cannot get back in."),
        ("Account suspended without warning", "We logged in this morning and the account is disabled."),
        ("Too many attempts message", "We are stuck on a lockout screen and the timer never clears."),
    ],
    "api_failure": [
        ("API returning errors", "Our integration is getting 500 errors on most calls."),
        ("API timing out", "Requests hang for thirty seconds and then fail."),
        ("Authentication failing on API", "Our key worked yesterday and is now rejected on every call."),
    ],
    "billing_error": [
        ("Charged the wrong amount", "The invoice does not match the plan we are on."),
        ("Double charged this month", "We have two identical charges on the same date."),
        ("Still being billed after cancelling", "We cancelled last month and a payment has gone out again."),
    ],
    "slow_performance": [
        ("The platform is very slow", "Pages take around thirty seconds to load."),
        ("Search is crawling", "Running a search takes almost a minute to return anything."),
        ("Slow since the update", "Everything has been sluggish since the change you made last week."),
    ],
    "integration_failure": [
        ("Integration stopped syncing", "Nothing has come through from the connected tool since Tuesday."),
        ("Connection keeps dropping", "The integration disconnects on its own every few hours."),
        ("Duplicate records from sync", "The sync is creating three copies of every record."),
    ],
    "notification_failure": [
        ("Not receiving emails", "Alert emails are not arriving in any of our inboxes."),
        ("Alerts stopped", "We used to get a notification for every new entry and they have gone quiet."),
        ("Notifications arriving late", "Alerts turn up about six hours after the thing happened."),
    ],
    "dashboard_bug": [
        ("Dashboard display problem", "One of the charts is showing the wrong labels."),
        ("Numbers do not match", "The total on the dashboard is different to the total in the report."),
        ("Chart will not load", "One panel stays blank no matter how many times I refresh."),
    ],
    "feature_request": [
        ("Feature suggestion", "It would help if we could sort the table by date."),
        ("Request for bulk actions", "Being able to select several rows at once would save us a lot of time."),
        ("Dark mode request", "Any chance of a dark theme, we work late most evenings."),
    ],
    "how_to_question": [
        ("How do I do this", "I cannot work out where to change the account settings."),
        ("Question about permissions", "How do I give a colleague access without making them an admin."),
        ("Where do I find my invoices", "I have looked in settings and cannot see a billing history anywhere."),
    ],
    "password_reset": [
        ("Password reset needed", "The reset link never arrives in my inbox."),
        ("Reset email not arriving", "I have requested a new password four times and nothing comes through."),
        ("New password not accepted", "I changed my password and now the new one is rejected."),
    ],
}

MOOD_OPENINGS = {
    "calm":    ["Hello,", "Hi there,", "Good morning,"],
    "annoyed": ["Hi,", "Hello again,", "Following up on this,"],
    "angry":   ["This is now the third time I am writing.", "This is unacceptable.", "We need this dealt with today."],
}

MOOD_CLOSINGS = {
    "calm":    ["Thanks for your help.", "No rush, whenever you get a chance.", "Many thanks."],
    "annoyed": ["Please could someone look at this.", "Hoping for a quick reply.", "This is holding us up."],
    "angry":   ["We are considering cancelling.", "Please escalate this immediately.", "We expect a reply today."],
}

print("Ticket wording created.")
# ----- SMALL HELPERS -----

def pick_weighted(options_with_chances):
    """
    Give it something like {"Low": 0.8, "Medium": 0.2} and it picks one option.
    Options with bigger numbers get picked more often.
    """
    names = list(options_with_chances.keys())
    chances = list(options_with_chances.values())
    return random.choices(names, weights=chances, k=1)[0]


def severity_as_number(severity):
    """Turn a severity word into a number so we can move it up or down a level."""
    return {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}[severity]


def severity_as_word(number):
    """Turn the number back into a word. Anything below 1 or above 4 gets pulled back in."""
    number = max(1, min(4, number))
    return {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}[number]


def check_the_lookup_tables():
    """
    Safety check. If any severity chances do not add up to 1, the maths is wrong.
    Better to find out now than after generating a thousand rows.
    """
    for issue_name, profile in ISSUE_PROFILES.items():
        total = sum(profile["sev"].values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Severity chances for '{issue_name}' add up to {total}, they must add up to 1")
    print("Lookup tables checked, all severity chances add up correctly.")


print("Helper functions created.")
# ----- STEP 1: make the customers (this becomes the CRM file) -----

COMPANY_WORDS_A = ["North", "Blue", "Iron", "Silver", "Green", "Bright", "Stone", "Clear", "Red", "Oak"]
COMPANY_WORDS_B = ["Bridge", "Harbour", "Field", "Works", "Labs", "Systems", "Group", "Partners", "Digital", "Retail"]


def make_customers():
    customers = []

    # Pull the plan names and how common each one is out of the lookup table.
    plan_names = list(CUSTOMER_PLANS.keys())
    plan_weights = [CUSTOMER_PLANS[name]["weight"] for name in plan_names]

    for i in range(1, HOW_MANY_CUSTOMERS + 1):
        plan = random.choices(plan_names, weights=plan_weights, k=1)[0]
        plan_details = CUSTOMER_PLANS[plan]

        customer = {
            "customer_id": f"CUST-{i:04d}",
            "company_name": f"{random.choice(COMPANY_WORDS_A)} {random.choice(COMPANY_WORDS_B)}",
            "plan": plan,
            "monthly_value_gbp": random.randint(plan_details["min_value"], plan_details["max_value"]),
            "months_as_customer": random.randint(1, 60),
            "promised_response_hours": plan_details["sla_hours"],
            "has_complained_before": random.random() < 0.25,
        }
        customers.append(customer)

    print(f"Made {len(customers)} customers.")
    return customers


print("Customer maker created.")
# ----- STEP 2: make one ticket -----
#
# This is where the interesting part happens. We work out three things:
#   - what the problem really is      (the true severity, which we never save)
#   - what mood the customer is in
#   - what severity the customer CLAIMS it is (they usually exaggerate)

def make_one_ticket(ticket_number, customer, times_this_customer_has_written):

    # Pick a problem type, using the freq numbers so common problems appear more often.
    issue_names = list(ISSUE_PROFILES.keys())
    issue_weights = [ISSUE_PROFILES[name]["freq"] for name in issue_names]
    issue_type = random.choices(issue_names, weights=issue_weights, k=1)[0]

    # How bad the problem actually is.
    true_severity = pick_weighted(ISSUE_PROFILES[issue_type]["sev"])

    # Decide the mood. People who have written several times already are crosser.
    if times_this_customer_has_written >= 3:
        mood = random.choices(["calm", "annoyed", "angry"], weights=[10, 35, 55], k=1)[0]
    elif times_this_customer_has_written == 2:
        mood = random.choices(["calm", "annoyed", "angry"], weights=[30, 50, 20], k=1)[0]
    else:
        mood = random.choices(["calm", "annoyed", "angry"], weights=[60, 32, 8], k=1)[0]

    # What the customer ticks in the severity dropdown. Angry people tick Critical.
    if mood == "angry":
        chance_of_exaggerating = 0.65
    elif mood == "annoyed":
        chance_of_exaggerating = 0.35
    else:
        chance_of_exaggerating = 0.10

    reported_severity = true_severity
    if random.random() < chance_of_exaggerating:
        bump = random.choice([1, 1, 2])
        reported_severity = severity_as_word(severity_as_number(true_severity) + bump)

    # Write the message. Pick one wording, then wrap it in a mood opening and closing.
    subject, middle_sentence = random.choice(TICKET_WORDING[issue_type])
    message = " ".join([
        random.choice(MOOD_OPENINGS[mood]),
        middle_sentence,
        random.choice(MOOD_CLOSINGS[mood]),
    ])

    # When it arrived. Somewhere in the last few months.
    hours_ago = random.randint(1, HOW_MANY_DAYS_OF_HISTORY * 24)
    created_at = datetime.now() - timedelta(hours=hours_ago)

    ticket = {
        "ticket_id": f"TICK-{ticket_number:05d}",
        "customer_id": customer["customer_id"],
        "created_at": created_at.strftime("%Y-%m-%d %H:%M"),
        "issue_type": issue_type,
        "subject": subject,
        "message": message,
        "reported_severity": reported_severity,
        "customer_mood": mood,
        "times_contacted_about_this": times_this_customer_has_written,
    }

    # We hand back the true severity separately so the next function can use it,
    # but it never goes into the ticket itself. Nobody knows the true answer
    # at the moment a ticket lands in the inbox.
    return ticket, true_severity


print("Ticket maker created.")
# ----- STEP 3: make the monitoring row (this becomes the telemetry file) -----
#
# Monitoring has no idea who the customer is. It only sees machines and numbers.

SERVICE_NAMES = ["auth-service", "billing-api", "export-worker", "web-app", "notify-service", "sync-engine"]


def make_telemetry_row(ticket, true_severity):

    # Some problems are never urgent, whatever severity was rolled for them.
    # We quieten these first, before anything else reads the severity.
    if ticket["issue_type"] in ["password_reset", "how_to_question", "feature_request"]:
        true_severity = "Low"

    # How many people are affected depends on how bad the problem really is.
    if true_severity == "Critical":
        affected_users = random.randint(200, 5000)
    elif true_severity == "High":
        affected_users = random.randint(20, 400)
    elif true_severity == "Medium":
        affected_users = random.randint(2, 40)
    else:
        affected_users = random.randint(1, 5)

    # Some problems only ever affect the one person who reported them.
    if ticket["issue_type"] in ["password_reset", "how_to_question", "feature_request", "compliance_request"]:
        affected_users = 1

    # Is the customer completely stuck, or just inconvenienced.
    blocking_problems = ["system_outage", "payment_failure", "account_lockout", "api_failure", "data_loss"]
    half_blocking_problems = ["login_failure", "integration_failure", "data_export_failure"]

    # These problems never stop anyone working. A dark mode request
    # is not blocking anybody, however keen they are on it.
    never_blocking_problems = ["feature_request", "how_to_question", "password_reset", "dashboard_bug"]

    if ticket["issue_type"] in never_blocking_problems:
        work_is_blocked = False
    elif ticket["issue_type"] in blocking_problems:
        work_is_blocked = random.random() < 0.8
    elif ticket["issue_type"] in half_blocking_problems:
        work_is_blocked = random.random() < 0.4
    else:
        work_is_blocked = random.random() < 0.05

    # What monitoring concludes, based only on what it can measure.
    if affected_users > 500 or (work_is_blocked and affected_users > 100):
        observed_severity = "Critical"
    elif affected_users > 50 or work_is_blocked:
        observed_severity = "High"
    elif affected_users > 5:
        observed_severity = "Medium"
    else:
        observed_severity = "Low"

   # Monitoring is blind to some problems. A security incident or a GDPR request
    # looks like absolutely nothing on a dashboard. This blind spot is deliberate.
    # If the dashboard cannot see the harm, it cannot see the affected users either,
    # so we quieten both numbers together.
    if ticket["issue_type"] in ["security_incident", "compliance_request", "billing_error"]:
        observed_severity = "Low"
        affected_users = random.randint(1, 3)

    # Error rate looks calm when nothing is measurably wrong, and spikes when it is.
    if observed_severity == "Low":
        error_rate = round(random.uniform(0, 8), 1)
    else:
        error_rate = round(random.uniform(5, 95), 1)

    return {
        "ticket_id": ticket["ticket_id"],
        "service_name": random.choice(SERVICE_NAMES),
        "affected_users": affected_users,
        "error_rate_percent": error_rate,
        "system_load_percent": random.randint(20, 99),
        "work_is_blocked": work_is_blocked,
        "observed_severity": observed_severity,
    }


print("Telemetry maker created.")
# ----- STEP 4: make the contract clock row (this becomes the SLA ledger file) -----
#
# SLA means Service Level Agreement. It is the promise in the contract,
# for example "we will reply to Enterprise customers within 2 hours".
# This source does not care what the problem is. It only watches the clock.

def make_sla_row(ticket, customer):

    promised_hours = customer["promised_response_hours"]

    # How long we actually took to send a first reply.
    # Most of the time we hit the target. Sometimes we miss it badly.
    if random.random() < 0.78:
        first_reply_hours = round(random.uniform(0.2, promised_hours * 0.9), 1)
    else:
        first_reply_hours = round(random.uniform(promised_hours, promised_hours * 4), 1)

    hours_left = round(promised_hours - first_reply_hours, 1)

    return {
        "ticket_id": ticket["ticket_id"],
        "customer_id": customer["customer_id"],
        "promised_response_hours": promised_hours,
        "first_reply_hours": first_reply_hours,
        "hours_left_before_promise_broken": hours_left,
        "promise_was_broken": first_reply_hours > promised_hours,
    }


print("SLA maker created.")
# ----- STEP 5: what a human eventually decided (this becomes the outcomes file) -----
#
# IMPORTANT: nothing in here is known at the moment a ticket arrives.
# Your agent must NEVER read this file when deciding an order.
# It is here so you can check the agent's decisions afterwards.

def make_outcome_row(ticket, customer, telemetry, sla):

    points = 0

    # Points for how bad it actually is, according to monitoring.
    points += {"Low": 0, "Medium": 2, "High": 5, "Critical": 9}[telemetry["observed_severity"]]

    # Points for how much the customer pays us.
    points += {"Free": 0, "Basic": 1, "Pro": 2, "Enterprise": 4}[customer["plan"]]

    # Points if the customer cannot work at all.
    if telemetry["work_is_blocked"]:
        points += 3

    # Points if the contract clock is nearly up, or already gone.
    if sla["promise_was_broken"]:
        points += 2
    elif sla["hours_left_before_promise_broken"] < 2:
        points += 3

    # Points if the customer has written about this repeatedly.
    if ticket["times_contacted_about_this"] >= 3:
        points += 2

    # Some problems get taken seriously no matter what monitoring saw.
    # This is the human overriding the dashboard.
    if ticket["issue_type"] in ["security_incident", "data_loss"]:
        points += 6
    if ticket["issue_type"] == "compliance_request":
        points += 3

    # Humans are not perfectly consistent, so nudge the score slightly at random.
    points += random.choice([-1, 0, 0, 1])

    # Turn the score into a priority from 1 (most urgent) to 4 (least urgent).
    if points >= 12:
        priority = 1
    elif points >= 8:
        priority = 2
    elif points >= 4:
        priority = 3
    else:
        priority = 4

    # Urgent tickets get fixed faster, but hard problems still take a while.
    typical_hours = {1: 4, 2: 12, 3: 48, 4: 120}[priority]
    hours_to_resolve = round(typical_hours * random.uniform(0.4, 2.2), 1)

    what_happened = random.choices(
        ["resolved", "escalated", "closed_no_action"],
        weights=[85, 10, 5],
        k=1,
    )[0]

    return {
        "ticket_id": ticket["ticket_id"],
        "priority_a_human_gave_it": priority,
        "hours_to_resolve": hours_to_resolve,
        "what_happened": what_happened,
    }


print("Outcome maker created.")
# ----- STEP 6: saving to CSV -----

def save_to_csv(rows, filename):
    """
    Takes a list of dictionaries and writes it out as a CSV file.
    The dictionary keys become the column headings.
    """
    # Create the "data" folder if it is not already there.
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    full_path = os.path.join(OUTPUT_FOLDER, filename)

    with open(full_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {full_path}")


print("CSV saver created.")
# ----- PUTTING IT ALL TOGETHER -----

def main():

    check_the_lookup_tables()

    customers = make_customers()

    # Empty lists to collect our rows into.
    tickets = []
    telemetry_rows = []
    sla_rows = []
    outcome_rows = []

    # Keeps count of how many times each customer has written to us.
    contact_counter = {}

    for ticket_number in range(1, HOW_MANY_TICKETS + 1):

        # Pick who is writing to us this time.
        customer = random.choice(customers)

        # Add one to their contact count.
        contact_counter[customer["customer_id"]] = contact_counter.get(customer["customer_id"], 0) + 1
        times_written = contact_counter[customer["customer_id"]]

        # Build the four rows for this one ticket.
        ticket, true_severity = make_one_ticket(ticket_number, customer, times_written)
        telemetry = make_telemetry_row(ticket, true_severity)
        sla = make_sla_row(ticket, customer)
        outcome = make_outcome_row(ticket, customer, telemetry, sla)

        tickets.append(ticket)
        telemetry_rows.append(telemetry)
        sla_rows.append(sla)
        outcome_rows.append(outcome)

    # Write everything out.
    save_to_csv(customers, "customers.csv")
    save_to_csv(tickets, "tickets.csv")
    save_to_csv(telemetry_rows, "telemetry.csv")
    save_to_csv(sla_rows, "sla_ledger.csv")
    save_to_csv(outcome_rows, "ticket_outcomes.csv")

    # A quick summary so you can sanity check without opening the files.
    print("\nQuick check on what we generated:")

    disagreements = 0
    for ticket, telemetry in zip(tickets, telemetry_rows):
        if ticket["reported_severity"] != telemetry["observed_severity"]:
            disagreements += 1
    print(f"  Tickets where the customer and monitoring disagree: {disagreements} out of {len(tickets)}")

    priority_counts = {}
    for row in outcome_rows:
        p = row["priority_a_human_gave_it"]
        priority_counts[p] = priority_counts.get(p, 0) + 1
    print(f"  Priority spread (1 is most urgent): {dict(sorted(priority_counts.items()))}")

    plan_counts = {}
    for c in customers:
        plan_counts[c["plan"]] = plan_counts.get(c["plan"], 0) + 1
    print(f"  Customer plans: {plan_counts}")


if __name__ == "__main__":
    main()