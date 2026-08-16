# Ticket Priority Agent

When several customer complaints are waiting at once, this decides which one a
person should deal with first, and explains why it chose that order.

---

## The problem

A support desk gets more complaints than it can answer at once. Somebody has to
decide what gets looked at first.

That sounds easy until you look at two real complaints side by side:

| | Complaint A | Complaint B |
|---|---|---|
| The customer pays us | £39,127 a month | Nothing. They are on the free plan |
| What is wrong | Pages load slowly | Their files have disappeared |
| How many people it affects | 3 | 4,940 |
| We promised to reply within | 2 hours | 72 hours |

Which one comes first?

If you go by money, the paying customer wins and thousands of people wait.
If you go by damage, the free customer wins and your biggest client is annoyed.
If you go by the promise you made, the paying customer wins again.

There is no calculation that settles this. Somebody has to make a judgement and
be able to defend it. That is what this project builds.

---

## The solution

An AI agent that:

1. Looks up three separate systems to find out what is really going on
2. Weighs four different ways of deciding what matters most
3. Reads what the customer actually wrote
4. Commits to one order and explains every position
5. Says out loud what it chose to favour and what that costs
6. Gets checked twice, in case it got something wrong

---

## The three systems it looks up

Real companies keep customer information in separate places, and each place
only knows part of the story. That is deliberate here, because it is what
creates the disagreement.

| System | What it knows | What it wants | What it cannot see |
|---|---|---|---|
| **Customer records** | Who they are, what plan they pay for | Look after whoever pays most | Whether anything is actually broken |
| **Monitoring** | How many people are affected, whether the system is failing | Fix whatever is most broken | Who the customer is, or what we promised them |
| **The promise clock** | How long we said we would take, how long is left | Answer whatever is closest to breaking a promise | Whether the complaint is important |

None of these three can see what the others see. So they routinely disagree,
and the agent has to work out who to believe.

### The blind spot, on purpose

Monitoring is deliberately made blind to three kinds of problem: suspected
break-ins, legal requests, and billing errors.

This is not a bug. Picture somebody who has stolen a password and is quietly
reading your files. Nothing is failing. Nobody has reported an error. The
monitoring screen is entirely green.

So the agent is given a case where every automatic warning light says
"nothing to see here" and the right answer is to deal with it immediately. The
only way to spot it is to read what the customer wrote.

---

## The four ways of deciding

Each one is reasonable. Each one is wrong on its own.

| Way of deciding | The question it asks | Who it helps | What it gets wrong |
|---|---|---|---|
| **Money** | Who pays us the most? | Big customers | Ignores a total failure for a small customer |
| **Damage** | What is most broken? | Whoever is worst affected | Ignores promises and contracts |
| **Deadline** | What promise breaks first? | Whoever has waited longest | Puts a trivial request above a break-in |
| **Fairness** | Who have we treated worst? | People we keep letting down | Slow to react to a real emergency |

The agent runs all four, then decides for itself. Its order is not a copy of
any one of them.

**This is the key result.** On the six test complaints, no two of the four ways
agree on what should come first:

| Complaint | Money | Damage | Deadline | Fairness |
|---|---|---|---|---|
| Slow pages, £39,127 customer | 1st | 3rd | 4th | 6th |
| Files disappeared, free customer | 6th | 1st | 3rd | 4th |
| Possible break-in, £55 customer | 4th | 4th | 5th | 2nd |
| Feature request, £29,044 customer | 2nd | 5th | 2nd | 3rd |
| Export broken, 50 hours late | 3rd | 2nd | 1st | 1st |
| Password reset, marked "Critical" | 5th | 6th | 6th | 5th |

Look at the first row. The same complaint is either the most urgent thing in
the queue or the least urgent, depending entirely on which way you pick.

---

## The written rules

Some things are too serious to leave to a judgement. These three rules are
written down separately, the way a real support desk keeps a policy document,
and they always apply:

| Rule | Why it is a rule and not a judgement |
|---|---|
| A suspected break-in is never below 3rd place | Monitoring cannot measure this kind of harm, so the numbers always underrate it |
| A legal request is never below 4th place | The deadline is set by law, not by us, and missing it means a fine |
| Somebody badly affected is never below 5th place just because they pay nothing | Paying nothing is not a reason to be left last when the problem is real |

Everything else is left to the agent's judgement, on purpose. Add enough fixed
rules and there is nothing left to think about.

---

## The two checks

The agent can get things wrong. So its answer is checked before anything
happens.

**Check one: did it follow the rules?**
Every complaint must come back exactly once, and the order must not break any
of the three written rules.

**Check two: are its reasons true?**
The agent explains each position in a sentence. This compares those sentences
against the actual numbers. If it says "affecting many users" about something
affecting three people, or "already overdue" about something with time left,
that gets caught.

**When a reason is wrong, it is sent back.**
The agent is told which claim the data does not support and asked to write that
reason again. If it still does not match after that, the whole decision is
flagged for a person to look at rather than being quietly accepted.

---

## What it produces

```
ORDER THE AGENT CHOSE
  1. TICK-00171  Massive data loss affecting thousands and blocking work.
  2. TICK-00982  Overdue by over two days and affecting dozens of users.
  3. TICK-00771  Possible break-in, which policy lifts into the top three.
  4. TICK-00266  Enterprise customer with a deadline 0.3 hours away.
  5. TICK-00707  High-paying, but only 3 users affected and nothing blocked.
  6. TICK-00135  Low impact password reset, plenty of time left.

THE TRADE-OFF
  We favoured damage over money, pushing high-paying but low-impact
  complaints down the queue. This may disappoint our biggest spenders but
  protects the people who are actually stuck.

HARDEST CALL
  Placing the break-in third rather than second was closest. Its seriousness
  could have justified a higher spot, but the export was already two days late.
```

Note positions 4 and 5. Two customers paying £68,171 a month between them sit
below a customer paying nothing. The agent says so, and says why.

---

## How to run it

You will need Python and a free Groq account for the API key.

**1. Get the code**
```bash
git clone https://github.com/kalpanajoycedovari/ticket-priority-agent.git
cd ticket-priority-agent
```

**2. Set up**
```bash
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn groq python-dotenv
```

On Mac or Linux, use `source venv/bin/activate` instead.

**3. Add your key**

Make a file called `.env` with one line in it:
```
GROQ_API_KEY=your_key_here
```

**4. Run it**
```bash
python decide.py
```

**Or run it as a web service**
```bash
uvicorn api:app --reload --port 8020
```

Then open http://127.0.0.1:8020/docs and press the button on `/decide`.

**To make fresh test data**
```bash
python generate_historical_data.py
python find_conflicts.py
python build_demo_batch.py
```

Those three build 1,000 pretend past complaints, find where the systems
disagree, and pick the six hardest cases out of them.

---

## The files

| File | What it does |
|---|---|
| `generate_historical_data.py` | Makes 1,000 pretend past complaints across five files |
| `find_conflicts.py` | Finds where the three systems disagree, and how often |
| `build_demo_batch.py` | Picks the six hardest cases out of the 1,000 |
| `brain.py` | Gathers the evidence and runs the four ways of deciding. Makes no decision |
| `decide.py` | Where the AI decides, explains itself, and gets checked |
| `api.py` | Puts it behind a web address |
| `data/` | The pretend complaints and the information about them |

---

## What is honest about this

The brief asked for a walkthrough of what is unfinished. These are the things I
would want a reviewer to know.

**The data is made up.** No real support data was available, so 1,000 past
complaints were generated. They were built carefully, but they are still
invented.

**One check partly detects my own writing.** The agent looks for phrases like
"this is the third time I am writing" to spot an unhappy customer. That phrase
came from the same script that wrote the pretend complaints, so the agent is
partly recognising my own words rather than real customer behaviour. The
phrases it uses to spot something serious are more defensible, because they
come from descriptions of the problem rather than the mood.

**The importance of each way of deciding is my choice.** Damage counts for
more than money in the scoring. That is a judgement I made, not a fact I
discovered, and somebody could reasonably weigh it differently.

**The AI does not always give the same answer.** Run it twice and the middle
positions can move. Every order it produced was defensible, but they were not
identical. Real consistency would need more work.

**One rule was read backwards, and I had to fix it.** A rule meant to protect
customers who pay nothing was originally named `never_below`. The AI read that
as a ceiling instead of a floor, and used it to push a complaint about 4,940
people's files disappearing down to fifth place, saying the policy required it.
A rule written to protect somebody was used to bury them. I renamed it to
`must_be_ranked_at_or_above` and spelled out in the rule itself that it only
ever lifts a complaint up, never pushes one down.

**The AI can be fooled by a loud customer.** In one run it placed a password
reset fourth because the customer had marked it "Critical", even though only
one person was affected and nothing was broken. The rule checks passed it,
because no written rule covers being taken in. This is exactly the kind of case
the reason checking was built for, and it does not catch all of them.

---

## What I would do next

In the order I would actually do it.

**1. Understand the words properly.**
Right now the agent looks for fixed phrases in the customer's message. That
works, but it is fragile, and as noted above it partly recognises my own
writing. Proper text understanding would let it tell the difference between
somebody who is genuinely describing a break-in and somebody who is just upset,
without relying on a list of phrases I chose.

**2. Handle complaints as they arrive, not in a batch.**
At the moment six complaints are decided together. A real desk gets one every
minute. That means the agent needs to slot a new arrival into a queue that is
already moving, and decide whether it is urgent enough to jump ahead of things
already waiting. That is a harder problem than sorting six at once.

**3. Learn from what people actually decided.**
There are 1,000 past complaints with the priority a person gave each one. A
model trained on those would give the agent a fifth opinion: "based on what
people did before, this usually goes second". It would be one more voice in the
argument, not the decider, and the agent would be able to overrule it in
writing. Worth being careful here, since those past decisions were generated by
a formula, so a model would mostly rediscover that formula rather than learn
anything real.

**4. Turn it into a full working pipeline.**
The pieces exist but they are not joined up. A complete version would be:

```
Complaint arrives  ->  look up all three systems at once
                   ->  AI decides where it belongs
                   ->  checks run
                   ->  passes: send to the right person
                   ->  fails: send to a human to review
                   ->  every decision saved with its reasoning
```

The last part matters most. Every decision, every reason, every time a check
caught something, saved and searchable. Six months later you could ask "how
often do we put paying customers behind free ones, and were we right to?" You
cannot ask that today, because nothing is kept.

---

Built as an assessment submission. The made-up data, the monitoring blind spot,
and both checks were my own decisions, and I can explain why I made each one.
