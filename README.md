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
7. Says how solid each decision was, and flags the close calls for a person
8. Keeps a permanent record of what it did, and writes it up in plain English

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

Each system is a separate file, joined together by the customer's reference
number, the same way separate systems join up in a real company. They were kept
separate on purpose. If everything sat in one big table, the agent would never
have to work out which source to believe, and there would be nothing to reason
about.

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

## How the practice data was made

No real support data was available, so 1,000 past complaints were built from
scratch. This was the largest part of the work, and the choices behind it
matter as much as the agent itself, because a queue where every answer is
obvious would prove nothing.

### Two separate dials for each kind of problem

An early version tied each kind of problem to a fixed list of allowed
seriousness levels. A payment failure could only ever be serious, a password
reset could only ever be minor.

That had to be thrown away. It meant the agent could skip straight from the
kind of problem to the answer, and the three systems became decoration.

The replacement gives every kind of problem two separate dials: how often it
turns up, and how bad it is likely to be when it does.

```python
ISSUE_PROFILES = {
    "system_outage":     {"freq": 1,  "sev": {"High": 0.2, "Critical": 0.8}},
    "security_incident": {"freq": 2,  "sev": {"Medium": 0.2, "High": 0.4, "Critical": 0.4}},
    "payment_failure":   {"freq": 8,  "sev": {"Medium": 0.3, "High": 0.5, "Critical": 0.2}},
    "slow_performance":  {"freq": 15, "sev": {"Low": 0.5, "Medium": 0.35, "High": 0.15}},
    "password_reset":    {"freq": 15, "sev": {"Low": 0.8, "Medium": 0.2}},
}
```

Reading one line: a payment failure turns up eight times as often as a total
outage, and when one appears there is a 30% chance it is medium, 50% high, 20%
critical. Seventeen kinds of problem are covered.

The frequency numbers matter as much as the seriousness ones. Real support
queues are mostly routine, with a thin sliver of emergencies. Password resets
turn up fifteen times as often as total outages, so the practice data looks
like a real inbox rather than a list of disasters.

### Two different opinions on how bad each problem is

Every complaint carries two separate seriousness ratings:

- **What the customer said** when they filled in the form
- **What monitoring worked out** from what it could actually measure

These disagree on 546 out of the 1,000 complaints.

That gap is the point. Customers exaggerate. Somebody who cannot reset their
password ticks "Critical" because to them it is critical. Monitoring sees one
person affected and nothing failing.

How much somebody exaggerates depends on their mood, and their mood depends
partly on how many times they have already written in:

```python
if mood == "angry":
    chance_of_exaggerating = 0.65
elif mood == "annoyed":
    chance_of_exaggerating = 0.35
else:
    chance_of_exaggerating = 0.10
```

So being loud does not mean being urgent, and the agent has to tell those apart
by reading the message rather than trusting the label.

### The true seriousness is thrown away

Each complaint is given a real seriousness when it is created. That is used to
work out what monitoring would have seen, and is then discarded. It is never
saved to any file.

Nobody knows the true answer at the moment a complaint arrives in real life, so
the agent does not get to know it either.

### What happened afterwards is kept in a separate file

A fifth file holds what a person eventually decided, how long it took to fix,
and how it ended. None of that is known when a complaint first arrives.

It is deliberately kept in its own file rather than as extra columns, so the
agent physically cannot read it while deciding. Doing that would be like
marking your own exam with the answers in front of you: the result would look
excellent and mean nothing.

That file is used afterwards, to compare what the agent chose against what a
person actually did.

### Three rounds of fixing data that made no sense

The first version produced combinations no reviewer would believe. Each was
found by printing real examples and reading them, rather than trusting the
summary numbers.

| What was wrong | Why it happened | The fix |
|---|---|---|
| A break-in showing 59 affected people while monitoring called it minor | The seriousness was quietened but the number of affected people was not | Quieten both together, so the story is consistent |
| A request for dark mode coming out as a serious problem | Any kind of problem had a small chance of "blocking work", and blocked work jumps straight to serious | List the problems that never block anyone |
| The deadline warning firing on nearly every large customer | The test asked for "fewer than 2 hours left" but large customers are only promised 2 hours in total, so it could never fail | Compare against a share of what was promised, not a fixed number of hours |

The last one is worth noting. One hour left means something very different for
a 2 hour promise and a 72 hour promise. Comparing raw hours would give you the
opposite of the truth.

---

## Where the three systems disagree, and how often

Rather than claiming the systems disagree, the disagreements were counted.
Eight kinds were named, and every one of the 1,000 complaints was tested
against them:

| Kind of disagreement | Count | What it means |
|---|---|---|
| We already broke our promise | 243 | We missed the reply time we agreed |
| Clock running out on something minor | 231 | Barely any time left, but the problem is trivial |
| Pays nothing but badly broken | 143 | Free customer, seriously affected or completely stuck |
| Customer overstating it | 139 | Claimed seriousness is two or more levels above what monitoring sees |
| Asked us again and again | 101 | Has written in seven or more times |
| Monitoring cannot see it | 61 | Break-in, legal request, or billing, where the screen stays green |
| Pays a lot, tiny problem | 46 | Pays £10,000 a month or more, nothing much is wrong |
| Customer understating it | 20 | Monitoring sees it as far worse than the customer said |

One tuning note. The "asked us again and again" test originally used four or
more contacts and fired on 425 out of 1,000. With 1,000 complaints across 200
customers, the average customer writes in five times, so almost everybody
tripped it. A warning that fires on 43% of cases is not a warning. Raising the
bar to seven brought it down to 101.

There is also a case where the labelling is knowingly naive. A legal data
deletion request from a customer paying £17,238 a month got labelled "pays a
lot, tiny problem", because "tiny" in that test means monitoring called it
minor, and monitoring is blind to legal work by design. That was left in rather
than patched. The labelling is simple and the agent has to be less simple than
the labelling.

---

## The six complaints given to the agent

Rather than writing the test cases by hand, a script searches all 1,000 for the
strongest real example of each kind of disagreement.

| Reference | The kind of case | Problem | Plan | Pays | Customer said | Monitoring said |
|---|---|---|---|---|---|---|
| TICK-00707 | Pays a lot, tiny problem | Slow pages | Enterprise | £39,127 | Low | Low |
| TICK-00171 | Free but badly broken | Files gone | Free | £0 | Critical | Critical |
| TICK-00771 | Monitoring cannot see it | Possible break-in | Basic | £55 | High | Low |
| TICK-00266 | Deadline nearly up | Feature request | Enterprise | £29,044 | High | Low |
| TICK-00982 | Asked before | Export broken | Basic | £106 | Medium | Medium |
| TICK-00135 | Overstated | Password reset | Basic | £41 | Critical | Low |

### Why this set is hard

Look at TICK-00135 and TICK-00771 side by side. On the numbers they are almost
identical: one person affected, monitoring says minor, customer claims it is
serious.

One is a password reset and belongs at the bottom. The other is somebody
reporting that their account email was changed without their knowledge, and
belongs near the top.

No amount of counting affected people separates those two. The only thing that
does is reading what the customer wrote. That pair is what stops the agent
taking an easy shortcut like "always believe the customer" or "always believe
monitoring", because both shortcuts fail here.

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

Two of the six are settled: the password reset is near the bottom under all
four, and the overdue export is near the top under all four. The other four are
genuinely contested, and the agent has to say which decisions were hard.

### Two details in the scoring worth explaining

**Damage does not grow in a straight line.** A complaint affecting 5,000 people
is not 5,000 times worse than one affecting one person. Every ten people count
as one point, so monitoring's own verdict stays the main signal and the count
of affected people only breaks ties. Without this, the complaint affecting
4,940 people would drown out every other number in the set.

**The deadline compares shares, not hours.** One hour left out of two promised
means most of your time is gone. One hour left out of seventy-two means you
have barely started. Comparing raw hours would rank those the wrong way round.

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

The rules live in one place and the code reads them from there, so a manager
could change the policy without touching the logic, and the two can never
quietly disagree with each other.

### What was deliberately left out

These were considered as fixed rules and rejected:

- Big customers always first
- Whatever affects most people always first
- Whatever is closest to a broken promise always first

Each one would remove a trade-off the agent is supposed to weigh. Enough fixed
rules and there is nothing left to think about, which is easier to attack than
a judgement that is explained in writing.

---

## The two checks

The agent can get things wrong. So its answer is checked before anything
happens.

**Check one: did it follow the rules?**
Every complaint must come back exactly once, and the order must not break any
of the three written rules. The "exactly once" part matters more than it looks.
An AI can drop a complaint, invent one, or list the same one twice. If that
happened, a customer would silently vanish from the queue.

**Check two: are its reasons true?**
The agent explains each position in a sentence. This compares those sentences
against the actual numbers. If it says "affecting many users" about something
affecting three people, or "already overdue" about something with time left,
that gets caught.

**When a reason is wrong, it is sent back.**
The agent is told which claim the data does not support and asked to write that
reason again. Only the wrong ones. If it rewrites the others anyway, those are
thrown away. If a reason still does not match after that, the whole decision is
flagged for a person to look at rather than being quietly accepted.

### Both checks catching something real

Neither check is decoration. Both have caught genuine mistakes.

**The rules check.** Ranking on numbers alone put the possible break-in fifth,
behind a request for bulk actions and a complaint about slow pages. The check
caught it:

```
TICK-00771 should move to position 3
  because monitoring cannot measure this kind of harm,
  so the numbers will always underrate it
```

**The reasons check.** The AI described a complaint as "many users blocked on
export" when monitoring showed nobody was blocked:

```
TICK-00982
  it said:           Late deadline and many users blocked on export
                     make it most urgent.
  but the data says: monitoring shows no work is blocked
```

The order was fine in that case. Only the explanation was wrong. Two different
kinds of failure, which is why there are two different checks.

---

## How solid is each decision?

An order is only half an answer. The other half is how much you should trust it.

Some decisions are close calls. If one number had been slightly different, the
complaint would have landed somewhere else entirely. Other decisions hold no
matter what you change. A support manager should know which is which, and
nothing in the agent said so.

So the project tests it directly.

### How the test works

For every complaint, one number is changed at a time, and the ranking is run
again to see whether the complaint moved.

The changes are small and believable, the kind of thing that could easily have
been slightly wrong in real life:

- Half as many people affected, or twice as many
- Work turns out to have been blocked after all, or not blocked after all
- A quarter more time left on the clock, or a quarter less
- The customer pays half what we recorded, or £20,000 a month more

Six or seven changes per complaint. If barely any of them move it, the decision
is solid. If several do, it was a close call.

### What it found

| Complaint | Where the scoring puts it | How solid | What moves it |
|---|---|---|---|
| Export broken, 50 hours late | 1st | **Solid** | Nothing. 0 of 7 changes move it |
| Files disappeared, free customer | 2nd | Fairly solid | 1 of 6 |
| Feature request, £29,044 customer | 3rd | Fairly solid | 2 of 6 |
| Slow pages, £39,127 customer | 4th | **Shaky** | 3 of 7 |
| Possible break-in, £55 customer | 5th | **Shaky** | 3 of 6 |
| Password reset, marked "Critical" | 6th | Fairly solid | 1 of 6 |

The overdue export at first place is completely solid. Seven different changes
and it does not budge. That is a decision you can act on without thinking twice.

The £39,127 customer at fourth is shaky. Three changes move it, and one moves it
two places. Its position is close to arbitrary, and that is worth knowing before
anybody explains it to that customer.

### It also produces the conditions that would reverse a decision

Because the test works by actually rerunning the ranking, it does not have to
guess what would change the answer. It knows:

```
TICK-00771  Possible break-in
  if 7 people were affected, not 1, it moves from 5 to 4
  if work was blocked after all,   it moves from 5 to 3
```

That is a real experiment, not the AI speculating. Somebody could take that
straight to a support team: check whether more than one account was touched,
because if it was, this moves up the queue.

### It flags the shaky ones for a person

The routing at the end says which decisions were not settled:

```
ROUTE TICK-00771 -> HUMAN AGENT  (now)      <- the scoring was not settled about this one
ROUTE TICK-00171 -> HUMAN AGENT  (next)
ROUTE TICK-00982 -> HUMAN AGENT  (next)
ROUTE TICK-00707 -> HUMAN AGENT  (queued)   <- the scoring was not settled about this one
```

Not every decision deserves the same amount of trust, and now the output says so.

### Two things this deliberately does not do

**It does not ask the AI again.** The test reruns the four ways of ranking, not
the AI. Asking the AI fifty times would be slow and costly, and the AI varies
between runs anyway, so there would be no way to tell whether an order moved
because of the change or because the AI happened to feel differently. The four
ways give the same answer every time, so anything that moves, moved because of
the change.

This means it measures how solid the **scoring** is, not how solid the AI's
final answer is. The AI decides on top of the scoring using the customer's own
words and the written rules, and this test cannot see either of those. The
output says so rather than overclaiming.

**The AI never sees the results.** They are worked out before it is asked to
decide, and deliberately kept from it. If the AI knew which decisions look
solid, it would start aiming to look solid rather than aiming to be right.

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

WHICH WAY OF RANKING IT LEANED CLOSEST TO
  Leaned towards: damage
  What money would have got right: correctly prioritised revenue, but would
    have pushed the critical data loss for a free customer down the queue
  What deadline would have got right: correctly surfaced overdue work, but
    could have left the break-in below where policy requires
  What fairness would have got right: correctly lifted the free customer, but
    ranks on how often somebody has written in rather than how bad it is
  What this leaning costs us: some high-paying customers wait longer, which
    risks losing them
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
pip install fastapi uvicorn groq python-dotenv python-docx
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

**To ask why one complaint ended up where it did**
```bash
python why.py TICK-00771
```

**To see how solid each decision is on its own**
```bash
python stability.py
```

**Or run it as a web service**
```bash
uvicorn api:app --reload --port 8020
```

Then open http://127.0.0.1:8020/docs and press the button on `/decide`.

**To make fresh practice data**
```bash
python generate_historical_data.py
python find_conflicts.py
python build_demo_batch.py
```

Those three build 1,000 pretend past complaints, count where the systems
disagree, and pick the six hardest cases out of them.

---

## The files

| File | What it does |
|---|---|
| `generate_historical_data.py` | Makes 1,000 pretend past complaints across five files |
| `find_conflicts.py` | Counts where the three systems disagree, in eight named ways |
| `build_demo_batch.py` | Picks the six hardest cases out of the 1,000 |
| `brain.py` | Gathers the evidence and runs the four ways of deciding. Makes no decision |
| `decide.py` | Where the AI decides, explains itself, and gets checked |
| `stability.py` | Tests which decisions were close calls, by changing one number at a time |
| `decision_log.py` | Saves every decision, with everything that went into it |
| `thinking_log.py` | Writes the same story into a Word file anyone can read |
| `why.py` | Looks up why one complaint was placed where it was |
| `api.py` | Puts it behind a web address |
| `data/customers.csv` | The customer records |
| `data/tickets.csv` | The complaints and what people wrote |
| `data/telemetry.csv` | What monitoring saw |
| `data/sla_ledger.csv` | The promise clock |
| `data/ticket_outcomes.csv` | What happened afterwards. Never read while deciding |
| `data/demo_batch.json` | The six complaints given to the agent |

`brain.py` gathers everything and picks no winner on purpose. That is the point
where the AI takes over, and keeping it separate means the evidence and the
judgement never get tangled together.

---

## Every decision is kept, and written up in plain English

A decision that is made, printed to a screen, and then gone is not much use to
a company. Six months later somebody asks why a customer was put fourth, and
there is no answer.

So every run is recorded twice, in two different ways, for two different
readers.

### For a computer: one file per decision

Each decision is saved as its own file under `data/decisions/`, holding
everything that went into it:

- what was known about every complaint at the time
- where each of the four ways of ranking placed it
- what the AI chose, and the reason it gave
- what the checks found, including any reason it had to rewrite
- how solid the answer was, and whether a person should look

Because the reasons **before** correction are kept alongside the corrected
ones, a log that quietly hides its own mistakes is not what this is.

There is a small tool for asking about one complaint:

```bash
python why.py TICK-00771
```

```
TICK-00771 appears in 2 decision(s).

  2026-08-16 16:34:45   (DEC-20260816-163445)
  Placed 2 out of 6
  Reason: Potential account takeover is a security risk that must be
          addressed within the top three.
  How solid that was: shaky
  Flagged for a person to look at.

  2026-08-16 16:37:16   (DEC-20260816-163716)
  Placed 2 out of 6
  Reason: A possible account takeover is a security risk that policy
          forces into the top three.
  How solid that was: shaky
  Flagged for a person to look at.
```

That output also shows something useful on its own: across two separate runs
the agent placed that complaint in the same position for the same reason, so
its judgement on that one is steady.

### For a person: a Word document that grows

`data/how_the_agent_thinks.docx` tells the same story the way somebody without
a technical background would want to read it. Each run is added underneath the
last, so the file becomes a history you can scroll back through.

It walks through seven steps in order:

1. The complaints that were waiting
2. What each of the three systems said about each one
3. How the four ways of ranking each ordered them, and where they clashed most
4. What the customers actually wrote
5. What the AI decided, why, and what it gave up
6. What the checks found
7. Where each complaint was routed

Here is the part worth reading, taken from a real run:

```
Were the reasons it gave actually true?

  TICK-00266 claimed: A feature request with a deadline in minutes is
                      urgent but less damaging than the overdue export.
  but the data says:  0.3 hours still remain

So the agent was asked to write those reasons again:

  TICK-00266 now reads: Its response window is nearly exhausted with only
                        0.3 hours left, and it comes from an enterprise
                        customer, so it sits above complaints with looser
                        deadlines.
```

The AI made a claim, the check caught it, the reason was rewritten, and all
three of those things are on permanent record. Nothing has to be taken on
trust.

### Why not a database?

A database would be the right answer for a reporting question, such as "how
often did we put paying customers behind free ones last quarter". It is the
wrong answer for "let me read what the agent was thinking", because nobody
opens a database to read a story.

The records are already stored as structured fields rather than loose text, so
moving them into Postgres later is a change of where they live, not a redesign.
Nothing in the reasoning depends on where the rows come from.

## What is honest about this

The brief asked for a walkthrough of what is unfinished. These are the things I
would want a reviewer to know.

**The data is made up.** No real support data was available, so 1,000 past
complaints were generated. They were built carefully and fixed three times
where they made no sense, but they are still invented.

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

**Asking for a favourite once made things worse.** An early version asked the
AI which of the four ways it chose. It answered "fairness" and then copied the
fairness ranking out almost exactly, including putting the £39,127 customer
last with the reason "is last under fairness". It had stopped judging and
started obeying. The wording was changed to ask which way its thinking leaned
closest to, after deciding, and the copying stopped.

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
anything real. That caveat would need saying out loud rather than presenting
the accuracy as a finding.

**4. Move the records into Postgres and join it all into one pipeline.**
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
