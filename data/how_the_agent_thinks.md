# How the agent thinks

Every time the agent decides which customer complaint should be handled first, what it did is written down here. The newest run is always at the bottom.

Each run walks through the same seven steps, in order, so you can see where the answer came from rather than just what it was.


---

## Run on 16 August 2026 at 21:49:58

*Recorded as DEC-20260816-214958*


### Step 1  Pick up the waiting complaints

6 complaints were waiting.

- `TICK-00707`  The platform is very slow
- `TICK-00171`  Deleted records we did not delete
- `TICK-00771`  Possible breach
- `TICK-00266`  Request for bulk actions
- `TICK-00982`  Cannot download report
- `TICK-00135`  Password reset needed

### Step 2  Look up the three separate systems

Each system knows a different part of the story, and none of them can see what the others see.

| Ticket | Customer records | Monitoring | The promise clock | They said |
|---|---|---|---|---|
| `TICK-00707` | Enterprise, £39,127/mo, asked 2x | Low, 3 affected, not blocked | 2.0h promised, 1.1h left | Low |
| `TICK-00171` | Free, £0/mo, asked 1x | Critical, 4940 affected, blocked | 72.0h promised, 29.6h left | Critical |
| `TICK-00771` | Basic, £55/mo, asked 7x | Low, 1 affected, not blocked | 24.0h promised, 15.4h left | High |
| `TICK-00266` | Enterprise, £29,044/mo, asked 4x | Low, 1 affected, not blocked | 2.0h promised, 0.3h left | High |
| `TICK-00982` | Basic, £106/mo, asked 11x | Medium, 35 affected, not blocked | 24.0h promised, -49.8h left, already late | Medium |
| `TICK-00135` | Basic, £41/mo, asked 1x | Low, 1 affected, not blocked | 24.0h promised, 19.3h left | Critical |

### Step 3  Rank them four different ways

Each way is reasonable on its own, and each one is wrong on its own. They are evidence for the agent to weigh, not instructions to follow.

- **money**: TICK-00707 → TICK-00266 → TICK-00982 → TICK-00771 → TICK-00135 → TICK-00171
- **damage**: TICK-00171 → TICK-00982 → TICK-00707 → TICK-00771 → TICK-00266 → TICK-00135
- **deadline**: TICK-00982 → TICK-00266 → TICK-00171 → TICK-00707 → TICK-00771 → TICK-00135
- **fairness**: TICK-00982 → TICK-00771 → TICK-00266 → TICK-00171 → TICK-00135 → TICK-00707

Where the four disagreed most:

- `TICK-00707` was placed as high as 1 and as low as 6. This is where judgement was needed.
- `TICK-00171` was placed as high as 1 and as low as 6. This is where judgement was needed.
- `TICK-00771` was placed as high as 2 and as low as 5. This is where judgement was needed.
- `TICK-00266` was placed as high as 2 and as low as 5. This is where judgement was needed.

### Step 4  Read what the customer actually wrote

The four ways above only look at numbers, so they cannot tell a password reset apart from a break-in. Both look like one person with nothing failing. The words are the difference.

- `TICK-00707`: "Hello, Pages take around thirty seconds to load. No rush, whenever you get a chance."
- `TICK-00171`: "Hi there, A folder of client files is gone and nobody on our side removed it. Many thanks."
- `TICK-00771`: "Hi, Someone has changed our admin email address and it was not us. Please could someone look at this."
- `TICK-00266`: "This is now the third time I am writing. Being able to select several rows at once would save us a lot of time. We expect a reply today."
- `TICK-00982`: "Hi, The export button spins for a while and then nothing happens. This is holding us up."
- `TICK-00135`: "This is now the third time I am writing. The reset link never arrives in my inbox. Please escalate this immediately."

### Step 5  The AI decides, and says why

**1. `TICK-00171`  Deleted records we did not delete**  
Massive data loss affecting thousands and blocking work makes it the top priority.

**2. `TICK-00982`  Cannot download report**  
The export failure is already overdue, so it must be addressed next.

**3. `TICK-00771`  Possible breach**  
A possible account takeover is a security risk that policy forces into the top three.

**4. `TICK-00266`  Request for bulk actions**  
The feature request is close to its promised response time.

**5. `TICK-00707`  The platform is very slow**  
Enterprise customer sees slow pages and system load is high, but impact is limited.

**6. `TICK-00135`  Password reset needed**  
A single password reset is low impact compared to other tickets.


**The contradictions it spotted:**

- `TICK-00171` money ranking (low) vs damage ranking (high). It believed damage, because The loss affected thousands of users and blocked work, which outweighs the customer's zero spend.
- `TICK-00771` monitoring severity (Low) vs customer claimed severity (High). It believed customer claim and policy, because A suspected account takeover cannot be measured by monitoring and policy mandates a high rank.
- `TICK-00135` customer claimed severity (Critical) vs monitoring severity (Low). It believed monitoring, because A password reset is a routine issue; the system shows only one user affected and no work blockage.

**The trade-off it made:** We favoured user impact and SLA breaches over pure revenue considerations, sacrificing some short‑term money optimisation. This may cost us a slight dip in immediate earnings but protects reputation and avoids larger fallout.

**The closest call:** Placing TICK-00982 second instead of first was hardest because its deadline is overdue, yet TICK-00171 harms far more users; either ordering could be justified.


**How it ranked the four ways of deciding:**

| Place | Way | Why here | What it gets wrong |
|---|---|---|---|
| 1 | damage | User impact and work blockage directly reflect service failure severity, which we prioritized for this batch. | It can push high‑paying customers with less visible impact down the list. |
| 2 | deadline | Missing promised response times erodes trust and may incur penalties, so SLA adherence was weighted next. | It may elevate tickets with low actual harm over more critical but not overdue issues. |
| 3 | fairness | Ensures equitable treatment, especially for security incidents that monitoring misses. | Fairness scores can conflict with revenue or impact metrics, leading to sub‑optimal resource use. |
| 4 | money | Revenue is important but was given the least weight because critical service failures outweigh profit in this set. | High‑value customers may feel deprioritized when their issues are less severe. |

### Step 6  Check the answer before anything happens

**Did every complaint come back, and were the written rules followed?**  
Yes. Nothing was dropped and no rule was broken.

**Were the reasons it gave actually true?**  
Yes. Every reason matched the numbers we hold.


**How solid was the answer?** One number was changed at a time and everything ranked again, to see which places were close calls.

| Ticket | How solid | Changes that move it |
|---|---|---|
| `TICK-00707` | shaky | 3 of 7 |
| `TICK-00171` | fairly solid | 1 of 6 |
| `TICK-00771` | shaky | 3 of 6 |
| `TICK-00266` | fairly solid | 2 of 6 |
| `TICK-00982` | solid | 0 of 7 |
| `TICK-00135` | fairly solid | 1 of 6 |

### Step 7  Hand them to a person

- `TICK-00171` goes to a person **now**
- `TICK-00982` goes to a person **next**
- `TICK-00771` goes to a person **next**  *(the numbers were not settled about this one)*
- `TICK-00266` goes to a person **queued**
- `TICK-00707` goes to a person **queued**  *(the numbers were not settled about this one)*
- `TICK-00135` goes to a person **queued**


---

## Run on 16 August 2026 at 22:16:41

*Recorded as DEC-20260816-221641*


### Step 1  Pick up the waiting complaints

5 complaints were waiting.

- `NEW-00001`  Team locked out of system
- `NEW-00002`  Customer data deletion request
- `NEW-00003`  Payments failing at checkout
- `NEW-00004`  Unknown device session
- `NEW-00005`  Dashboard showing outdated data

### Step 2  Look up the three separate systems

Each system knows a different part of the story, and none of them can see what the others see.

| Ticket | Customer records | Monitoring | The promise clock | They said |
|---|---|---|---|---|
| `NEW-00001` | Enterprise, £27,928/mo, asked 1x | Critical, 1676 affected, blocked | 2.0h promised, 1.6h left | Critical |
| `NEW-00002` | Basic, £119/mo, asked 1x | Low, 2 affected, not blocked | 24.0h promised, 18.7h left | High |
| `NEW-00003` | Basic, £104/mo, asked 1x | Critical, 2026 affected, blocked | 24.0h promised, 0.5h left | High |
| `NEW-00004` | Basic, £56/mo, asked 1x | Low, 2 affected, not blocked | 24.0h promised, -5.3h left, already late | Low |
| `NEW-00005` | Free, £0/mo, asked 1x | Medium, 36 affected, not blocked | 72.0h promised, -3.5h left, already late | Critical |

### Step 3  Rank them four different ways

Each way is reasonable on its own, and each one is wrong on its own. They are evidence for the agent to weigh, not instructions to follow.

- **money**: NEW-00001 → NEW-00002 → NEW-00003 → NEW-00004 → NEW-00005
- **damage**: NEW-00003 → NEW-00001 → NEW-00005 → NEW-00002 → NEW-00004
- **deadline**: NEW-00004 → NEW-00005 → NEW-00003 → NEW-00002 → NEW-00001
- **fairness**: NEW-00004 → NEW-00005 → NEW-00002 → NEW-00003 → NEW-00001

Where the four disagreed most:

- `NEW-00001` was placed as high as 1 and as low as 5. This is where judgement was needed.
- `NEW-00003` was placed as high as 1 and as low as 4. This is where judgement was needed.
- `NEW-00004` was placed as high as 1 and as low as 5. This is where judgement was needed.
- `NEW-00005` was placed as high as 2 and as low as 5. This is where judgement was needed.

### Step 4  Read what the customer actually wrote

The four ways above only look at numbers, so they cannot tell a password reset apart from a break-in. Both look like one person with nothing failing. The words are the difference.

- `NEW-00001`: "our whole team is locked out. nobody can get in since about 6am. we have a client demo at 10 and I don't know what to tell them"
- `NEW-00002`: "I need to flag something. one of our customers has asked us to delete everything we hold on them. I believe there's a legal time limit on this and we're already a few days in"
- `NEW-00003`: "payments are failing at checkout. we've had maybe forty customers email us this morning saying their card was declined. our own test card fails too"
- `NEW-00004`: "there is a session logged in from a device we don't recognise and I can't work out how to end it. probably nothing but thought I should mention it"
- `NEW-00005`: "ABSOLUTELY UNACCEPTABLE. our dashboard chart is showing last month's figures. we pay you thousands every month and I expect better than this. I want someone to call me today"

### Step 5  The AI decides, and says why

**1. `NEW-00001`  Team locked out of system**  
High‑paying enterprise with a critical lockout affecting the whole team and a looming demo, so it gets top priority.

**2. `NEW-00003`  Payments failing at checkout**  
Critical payment failures block thousands of customers and the SLA is almost due, placing it second.

**3. `NEW-00004`  Unknown device session**  
A possible security breach is flagged by policy to be at least third, and the deadline is already missed.

**4. `NEW-00002`  Customer data deletion request**  
Legal data‑deletion request must be handled within the SLA but is less urgent than the above issues.

**5. `NEW-00005`  Dashboard showing outdated data**  
Dashboard showing stale data affects a free user and, despite being overdue, ranks last after higher‑impact tickets.


**The contradictions it spotted:**

- `NEW-00001` money/damage rankings put it high while deadline/fairness ranked it low. It believed money/damage, because The customer pays enterprise rates and the lockout blocks all work, outweighing the still‑available SLA time.
- `NEW-00003` damage ranking placed it first but money ranking placed it third. It believed damage, because The sheer number of affected users and complete work blockage make the impact larger than the modest revenue.
- `NEW-00004` deadline/fairness ranked it first but money/damage ranked it last. It believed deadline/fairness and policy rule for suspected break‑ins, because Policy forces a security incident to be at least third and the missed deadline signals urgency despite low revenue.

**The trade-off it made:** We favoured revenue (money) and user impact (damage) over the tighter remaining SLA on the payment‑failure ticket, pushing it to second place. This sacrifices a few minutes of SLA compliance on the payment issue, risking a minor breach cost.

**The closest call:** Choosing between NEW-00001 and NEW-00003 was tight; the lockout’s high revenue and upcoming demo versus the payment failure’s larger user base and nearer deadline could both justify top rank.


**How it ranked the four ways of deciding:**

| Place | Way | Why here | What it gets wrong |
|---|---|---|---|
| 1 | damage | User impact and work blockage affected the most customers in this batch, driving the priority order. | It can over‑prioritise low‑paying customers at the expense of revenue considerations. |
| 2 | money | Revenue size is a strong business signal, especially for the enterprise lockout. | It may push critical but low‑paying issues down too far. |
| 3 | deadline | Approaching or missed SLA deadlines indicate urgency that must be respected. | Deadlines alone ignore the scale of impact or revenue. |
| 4 | fairness | Ensures equal treatment across customers but is less decisive when other signals clash. | Can dilute priority for truly urgent or high‑impact cases. |

### Step 6  Check the answer before anything happens

**Did every complaint come back, and were the written rules followed?**  
Yes. Nothing was dropped and no rule was broken.

**Were the reasons it gave actually true?**  
Yes. Every reason matched the numbers we hold.


**How solid was the answer?** One number was changed at a time and everything ranked again, to see which places were close calls.

| Ticket | How solid | Changes that move it |
|---|---|---|
| `NEW-00001` | fairly solid | 2 of 7 |
| `NEW-00002` | fairly solid | 1 of 7 |
| `NEW-00003` | fairly solid | 2 of 7 |
| `NEW-00004` | shaky | 3 of 7 |
| `NEW-00005` | fairly solid | 1 of 6 |

### Step 7  Hand them to a person

- `NEW-00001` goes to a person **now**
- `NEW-00003` goes to a person **next**
- `NEW-00004` goes to a person **next**  *(the numbers were not settled about this one)*
- `NEW-00002` goes to a person **queued**
- `NEW-00005` goes to a person **queued**


---

## Run on 16 August 2026 at 22:20:49

*Recorded as DEC-20260816-222049*


### Step 1  Pick up the waiting complaints

5 complaints were waiting.

- `NEW-00001`  Team locked out
- `NEW-00002`  Customer data deletion request
- `NEW-00003`  Payments failing at checkout
- `NEW-00004`  Unknown device session
- `NEW-00005`  Dashboard showing outdated data

### Step 2  Look up the three separate systems

Each system knows a different part of the story, and none of them can see what the others see.

| Ticket | Customer records | Monitoring | The promise clock | They said |
|---|---|---|---|---|
| `NEW-00001` | Free, £0/mo, asked 1x | Critical, 2860 affected, blocked | 72.0h promised, 2.9h left | Critical |
| `NEW-00002` | Free, £0/mo, asked 1x | Low, 1 affected, not blocked | 72.0h promised, 12.0h left | High |
| `NEW-00003` | Free, £0/mo, asked 1x | Critical, 1306 affected, blocked | 72.0h promised, 48.3h left | High |
| `NEW-00004` | Free, £0/mo, asked 1x | Low, 1 affected, not blocked | 72.0h promised, 61.6h left | Low |
| `NEW-00005` | Free, £0/mo, asked 1x | Low, 16 affected, not blocked | 72.0h promised, 62.2h left | High |

### Step 3  Rank them four different ways

Each way is reasonable on its own, and each one is wrong on its own. They are evidence for the agent to weigh, not instructions to follow.

- **money**: NEW-00001 → NEW-00002 → NEW-00003 → NEW-00004 → NEW-00005
- **damage**: NEW-00001 → NEW-00003 → NEW-00005 → NEW-00002 → NEW-00004
- **deadline**: NEW-00001 → NEW-00002 → NEW-00003 → NEW-00004 → NEW-00005
- **fairness**: NEW-00001 → NEW-00002 → NEW-00003 → NEW-00004 → NEW-00005

Where the four disagreed most:


### Step 4  Read what the customer actually wrote

The four ways above only look at numbers, so they cannot tell a password reset apart from a break-in. Both look like one person with nothing failing. The words are the difference.

- `NEW-00001`: "our whole team is locked out. nobody can get in since about 6am. we have a client demo at 10 and I don't know what to tell them"
- `NEW-00002`: "I need to flag something. one of our customers has asked us to delete everything we hold on them. I believe there's a legal time limit on this and we're already a few days in"
- `NEW-00003`: "payments are failing at checkout. we've had maybe forty customers email us this morning saying their card was declined. our own test card fails too"
- `NEW-00004`: "there is a session logged in from a device we don't recognise and I can't work out how to end it. probably nothing but thought I should mention it"
- `NEW-00005`: "ABSOLUTELY UNACCEPTABLE. our dashboard chart is showing last month's figures. we pay you thousands every month and I expect better than this. I want someone to call me today"

### Step 5  The AI decides, and says why

**1. `NEW-00001`  Team locked out**  
Critical lockout affecting thousands and blocking work with only 2.9 h left makes it top priority.

**2. `NEW-00003`  Payments failing at checkout**  
Payments failing blocks revenue for over a thousand users and is critical, though deadline is farther out.

**3. `NEW-00004`  Unknown device session**  
Potential security breach triggers policy requiring at‑least top‑3 placement despite low monitored severity.

**4. `NEW-00002`  Customer data deletion request**  
Legal GDPR deletion request must be handled within the statutory window, so it ranks high.

**5. `NEW-00005`  Dashboard showing outdated data**  
Dashboard showing stale data affects few users and is not blocked, so it stays last.


**The contradictions it spotted:**

- `NEW-00002` customer claimed High severity vs monitoring Low severity. It believed legal/compliance requirement (policy), because the law‑mandated deadline outweighs subjective severity assessments
- `NEW-00004` monitoring low severity vs policy for suspected break‑in demanding top‑3. It believed policy uplift for security incidents, because monitoring cannot see the hidden risk of a takeover, so policy is more reliable
- `NEW-00005` customer claimed High severity vs monitoring Low severity. It believed monitoring data, because the issue affects few users and does not block work, making the low impact more trustworthy

**The trade-off it made:** We favored immediate business impact and security/legal compliance over fairness to free‑plan customers and monetary value. This sacrifices quicker service for paying customers, costing potential goodwill from high‑paying accounts.

**The closest call:** Choosing between the security incident (NEW-00004) and the GDPR request (NEW-00002) was hardest; both have mandatory uplift rules and either could reasonably sit at position three.


**How it ranked the four ways of deciding:**

| Place | Way | Why here | What it gets wrong |
|---|---|---|---|
| 1 | damage | User impact and work blockage are the clearest signs of business harm for this batch | It can under‑weight legal deadlines that are critical regardless of user count |
| 2 | deadline | Time left before promised resolution directly drives urgency | It ignores the scale of impact, so a far‑away deadline on a massive outage might be deprioritized |
| 3 | fairness | Ensures free‑plan customers with real problems are not pushed to the bottom | May elevate low‑impact tickets above higher‑value ones |
| 4 | money | Revenue is least relevant when critical functionality is broken | Could delay attention to high‑paying customers whose issues also affect revenue |

### Step 6  Check the answer before anything happens

**Did every complaint come back, and were the written rules followed?**  
Yes. Nothing was dropped and no rule was broken.

**Were the reasons it gave actually true?**  
Yes. Every reason matched the numbers we hold.


**How solid was the answer?** One number was changed at a time and everything ranked again, to see which places were close calls.

| Ticket | How solid | Changes that move it |
|---|---|---|
| `NEW-00001` | solid | 0 of 6 |
| `NEW-00002` | fairly solid | 2 of 5 |
| `NEW-00003` | fairly solid | 1 of 6 |
| `NEW-00004` | shaky | 4 of 5 |
| `NEW-00005` | solid | 0 of 6 |

### Step 7  Hand them to a person

- `NEW-00001` goes to a person **now**
- `NEW-00003` goes to a person **next**
- `NEW-00004` goes to a person **next**  *(the numbers were not settled about this one)*
- `NEW-00002` goes to a person **queued**
- `NEW-00005` goes to a person **queued**


---

## Run on 17 August 2026 at 13:38:59

*Recorded as DEC-20260817-133859*


### Step 1  Pick up the waiting complaints

5 complaints were waiting.

- `NEW-00001`  Team locked out
- `NEW-00002`  Customer data deletion request
- `NEW-00003`  Payments failing at checkout
- `NEW-00004`  Unknown device session
- `NEW-00005`  Dashboard showing outdated data

### Step 2  Look up the three separate systems

Each system knows a different part of the story, and none of them can see what the others see.

| Ticket | Customer records | Monitoring | The promise clock | They said |
|---|---|---|---|---|
| `NEW-00001` | Free, £0/mo, asked 1x | Critical, 2860 affected, blocked | 72.0h promised, 2.9h left | Critical |
| `NEW-00002` | Free, £0/mo, asked 1x | Low, 1 affected, not blocked | 72.0h promised, 12.0h left | High |
| `NEW-00003` | Free, £0/mo, asked 1x | Critical, 1306 affected, blocked | 72.0h promised, 48.3h left | High |
| `NEW-00004` | Free, £0/mo, asked 1x | Low, 1 affected, not blocked | 72.0h promised, 61.6h left | Low |
| `NEW-00005` | Free, £0/mo, asked 1x | Low, 16 affected, not blocked | 72.0h promised, 62.2h left | High |

### Step 3  Rank them four different ways

Each way is reasonable on its own, and each one is wrong on its own. They are evidence for the agent to weigh, not instructions to follow.

- **money**: NEW-00001 → NEW-00002 → NEW-00003 → NEW-00004 → NEW-00005
- **damage**: NEW-00001 → NEW-00003 → NEW-00005 → NEW-00002 → NEW-00004
- **deadline**: NEW-00001 → NEW-00002 → NEW-00003 → NEW-00004 → NEW-00005
- **fairness**: NEW-00001 → NEW-00002 → NEW-00003 → NEW-00004 → NEW-00005

Where the four disagreed most:


### Step 4  Read what the customer actually wrote

The four ways above only look at numbers, so they cannot tell a password reset apart from a break-in. Both look like one person with nothing failing. The words are the difference.

- `NEW-00001`: "our whole team is locked out. nobody can get in since about 6am. we have a client demo at 10 and I don't know what to tell them"
- `NEW-00002`: "I need to flag something. one of our customers has asked us to delete everything we hold on them. I believe there's a legal time limit on this and we're already a few days in"
- `NEW-00003`: "payments are failing at checkout. we've had maybe forty customers email us this morning saying their card was declined. our own test card fails too"
- `NEW-00004`: "there is a session logged in from a device we don't recognise and I can't work out how to end it. probably nothing but thought I should mention it"
- `NEW-00005`: "ABSOLUTELY UNACCEPTABLE. our dashboard chart is showing last month's figures. we pay you thousands every month and I expect better than this. I want someone to call me today"

### Step 5  The AI decides, and says why

**1. `NEW-00001`  Team locked out**  
Critical team lockout affecting all users and blocking work with a demo in hours forces it to the top.

**2. `NEW-00003`  Payments failing at checkout**  
Widespread payment failures block transactions for many users, making it the next priority.

**3. `NEW-00004`  Unknown device session**  
Potential security breach, despite low monitored impact, is lifted by policy to at least third place.

**4. `NEW-00002`  Customer data deletion request**  
Legal data deletion request must be handled within statutory time, so it stays within the top four.

**5. `NEW-00005`  Dashboard showing outdated data**  
Dashboard showing stale data impacts few users and can wait behind higher‑impact issues.


**The contradictions it spotted:**

- `NEW-00002` monitoring severity Low vs customer claimed High and damage ranking 4. It believed monitoring data for actual impact but policy for legal urgency, because monitoring reflects real system effect, while the legal deadline forces a higher priority regardless of impact
- `NEW-00004` damage ranking 5 (low) vs policy requiring at least position 3 for suspected break‑in. It believed policy rule, because Policy explicitly lifts security‑related tickets above the damage‑only view to guard against blind spots
- `NEW-00005` fairness ranking 5 (low) vs damage ranking 3 (higher). It believed damage ranking, because The actual number of affected users (16) is modest, so impact outweighs the subjective fairness claim

**The trade-off it made:** We favoured impact and security/legal risk over pure monitoring severity and customer‑expressed urgency. This means a low‑severity security alert jumps ahead of a legal request, costing a slight delay on the compliance ticket but protecting the platform and avoiding possible breach penalties.

**The closest call:** Balancing the legal deletion request (NEW-00002) against the suspected security incident (NEW-00004) was toughest; either could be justified as third, but we placed security higher to respect the explicit policy lift.


**How it ranked the four ways of deciding:**

| Place | Way | Why here | What it gets wrong |
|---|---|---|---|
| 1 | damage | Impact on users and work blockage directly affect business continuity, which was the dominant factor across tickets. | It can undervalue legal or security obligations that have low immediate user impact but high downstream risk |
| 2 | deadline | Statutory and SLA deadlines dictate urgency beyond raw impact, especially for compliance tickets. | May push a less‑critical but time‑sensitive request ahead of a higher‑impact incident |
| 3 | fairness | Considers customer sentiment and equity, useful when impact metrics are similar. | Subjective and can be skewed by angry customers exaggerating severity |
| 4 | money | All tickets are from free plans, so revenue provides no useful differentiation. | Ignores potential long‑term value of high‑paying customers, though not relevant here |

### Step 6  Check the answer before anything happens

**Did every complaint come back, and were the written rules followed?**  
Yes. Nothing was dropped and no rule was broken.

**Were the reasons it gave actually true?**  
Yes. Every reason matched the numbers we hold.


**How solid was the answer?** One number was changed at a time and everything ranked again, to see which places were close calls.

| Ticket | How solid | Changes that move it |
|---|---|---|
| `NEW-00001` | solid | 0 of 6 |
| `NEW-00002` | fairly solid | 2 of 5 |
| `NEW-00003` | fairly solid | 1 of 6 |
| `NEW-00004` | shaky | 4 of 5 |
| `NEW-00005` | solid | 0 of 6 |

### Step 7  Hand them to a person

- `NEW-00001` goes to a person **now**
- `NEW-00003` goes to a person **next**
- `NEW-00004` goes to a person **next**  *(the numbers were not settled about this one)*
- `NEW-00002` goes to a person **queued**
- `NEW-00005` goes to a person **queued**


---

## Run on 17 August 2026 at 13:51:28

*Recorded as DEC-20260817-135128*


### Step 1  Pick up the waiting complaints

5 complaints were waiting.

- `NEW-00001`  Team locked out
- `NEW-00002`  Customer data deletion request
- `NEW-00003`  Payments failing at checkout
- `NEW-00004`  Unknown device session
- `NEW-00005`  Dashboard showing outdated data

### Step 2  Look up the three separate systems

Each system knows a different part of the story, and none of them can see what the others see.

| Ticket | Customer records | Monitoring | The promise clock | They said |
|---|---|---|---|---|
| `NEW-00001` | Free, £0/mo, asked 1x | Critical, 2860 affected, blocked | 72.0h promised, 2.9h left | Critical |
| `NEW-00002` | Free, £0/mo, asked 1x | Low, 1 affected, not blocked | 72.0h promised, 12.0h left | High |
| `NEW-00003` | Free, £0/mo, asked 1x | Critical, 1306 affected, blocked | 72.0h promised, 48.3h left | High |
| `NEW-00004` | Free, £0/mo, asked 1x | Low, 1 affected, not blocked | 72.0h promised, 61.6h left | Low |
| `NEW-00005` | Free, £0/mo, asked 1x | Low, 16 affected, not blocked | 72.0h promised, 62.2h left | High |

### Step 3  Rank them four different ways

Each way is reasonable on its own, and each one is wrong on its own. They are evidence for the agent to weigh, not instructions to follow.

- **money**: NEW-00001 → NEW-00002 → NEW-00003 → NEW-00004 → NEW-00005
- **damage**: NEW-00001 → NEW-00003 → NEW-00005 → NEW-00002 → NEW-00004
- **deadline**: NEW-00001 → NEW-00002 → NEW-00003 → NEW-00004 → NEW-00005
- **fairness**: NEW-00001 → NEW-00002 → NEW-00003 → NEW-00004 → NEW-00005

Where the four disagreed most:


### Step 4  Read what the customer actually wrote

The four ways above only look at numbers, so they cannot tell a password reset apart from a break-in. Both look like one person with nothing failing. The words are the difference.

- `NEW-00001`: "our whole team is locked out. nobody can get in since about 6am. we have a client demo at 10 and I don't know what to tell them"
- `NEW-00002`: "I need to flag something. one of our customers has asked us to delete everything we hold on them. I believe there's a legal time limit on this and we're already a few days in"
- `NEW-00003`: "payments are failing at checkout. we've had maybe forty customers email us this morning saying their card was declined. our own test card fails too"
- `NEW-00004`: "there is a session logged in from a device we don't recognise and I can't work out how to end it. probably nothing but thought I should mention it"
- `NEW-00005`: "ABSOLUTELY UNACCEPTABLE. our dashboard chart is showing last month's figures. we pay you thousands every month and I expect better than this. I want someone to call me today"

### Step 5  The AI decides, and says why

**1. `NEW-00001`  Team locked out**  
Critical lockout affecting all users and a pending demo forces it to the top.

**2. `NEW-00003`  Payments failing at checkout**  
Widespread payment failures block commerce for many customers, demanding immediate attention.

**3. `NEW-00004`  Unknown device session**  
Potential security breach, even if low‑severity now, is lifted by policy to be handled within the top three.

**4. `NEW-00002`  Customer data deletion request**  
Legal GDPR deletion request must be addressed promptly to avoid fines, placing it just below the top three.

**5. `NEW-00005`  Dashboard showing outdated data**  
Dashboard showing stale data impacts a small set of users and is low priority after higher‑impact issues.


**The contradictions it spotted:**

- `NEW-00002` customer claimed High severity vs monitoring Low severity. It believed monitoring, because monitoring reflects actual system impact, while the customer's urgency is driven by legal deadline already captured elsewhere.
- `NEW-00005` customer claimed High severity vs monitoring Low severity. It believed monitoring, because the issue affects only 16 users and does not block work, so monitoring's low rating is more reliable.
- `NEW-00004` damage ranking placed it 5th vs policy requiring top‑3. It believed policy, because policy explicitly lifts suspected security incidents regardless of measured damage.

**The trade-off it made:** We favored impact and legal risk over pure fairness and monetary considerations, meaning we may delay less urgent but still important fairness concerns, costing us a slower response to the disgruntled dashboard user.

**The closest call:** Choosing whether the security incident (NEW-00004) or the GDPR request (NEW-00002) should be third was hardest, as both have strong arguments; we placed the security incident higher due to the policy lift, but the legal deadline could also justify a higher rank.


**How it ranked the four ways of deciding:**

| Place | Way | Why here | What it gets wrong |
|---|---|---|---|
| 1 | damage | Impact on users and business continuity varied widely and directly reflects the urgency of the problem. | It can undervalue legal deadlines or policy lifts that are not captured by raw damage numbers. |
| 2 | deadline | Remaining SLA time influences how quickly we must act, especially for near‑deadline tickets. | Deadlines may be generous for low‑impact issues, causing them to outrank more critical technical failures. |
| 3 | fairness | Ensures equal treatment of all customers regardless of payment, but is less decisive when impact differs sharply. | May promote lower‑impact tickets over higher‑impact ones. |
| 4 | money | All tickets are from free plans, so monetary weighting adds little useful signal. | Ignores the fact that paying customers might deserve faster service, but here it would mislead. |

### Step 6  Check the answer before anything happens

**Did every complaint come back, and were the written rules followed?**  
Yes. Nothing was dropped and no rule was broken.

**Were the reasons it gave actually true?**  
Yes. Every reason matched the numbers we hold.


**How solid was the answer?** One number was changed at a time and everything ranked again, to see which places were close calls.

| Ticket | How solid | Changes that move it |
|---|---|---|
| `NEW-00001` | solid | 0 of 6 |
| `NEW-00002` | fairly solid | 2 of 5 |
| `NEW-00003` | fairly solid | 1 of 6 |
| `NEW-00004` | shaky | 4 of 5 |
| `NEW-00005` | solid | 0 of 6 |

### Step 7  Hand them to a person

- `NEW-00001` goes to a person **now**
- `NEW-00003` goes to a person **next**
- `NEW-00004` goes to a person **next**  *(the numbers were not settled about this one)*
- `NEW-00002` goes to a person **queued**
- `NEW-00005` goes to a person **queued**


---

## Run on 19 August 2026 at 20:15:43

*Recorded as DEC-20260819-201543*


### Step 1  Pick up the waiting complaints

5 complaints were waiting.

- `NEW-00001`  Team locked out
- `NEW-00002`  Customer data deletion request
- `NEW-00003`  Payments failing at checkout
- `NEW-00004`  Unrecognized device session
- `NEW-00005`  Dashboard showing outdated data

### Step 2  Look up the three separate systems

Each system knows a different part of the story, and none of them can see what the others see.

| Ticket | Customer records | Monitoring | The promise clock | They said |
|---|---|---|---|---|
| `NEW-00001` | Enterprise, £27,928/mo, asked 1x | Critical, 882 affected, blocked | 2.0h promised, 0.7h left | Critical |
| `NEW-00002` | Pro, £540/mo, asked 1x | Low, 1 affected, not blocked | 8.0h promised, 4.1h left | High |
| `NEW-00003` | Free, £0/mo, asked 1x | Critical, 2155 affected, blocked | 72.0h promised, 4.6h left | Critical |
| `NEW-00004` | Free, £0/mo, asked 1x | Low, 3 affected, not blocked | 72.0h promised, -27.8h left, already late | Low |
| `NEW-00005` | Free, £0/mo, asked 1x | Low, 10 affected, not blocked | 72.0h promised, -42.6h left, already late | Critical |

### Step 3  Rank them four different ways

Each way is reasonable on its own, and each one is wrong on its own. They are evidence for the agent to weigh, not instructions to follow.

- **money**: NEW-00001 → NEW-00002 → NEW-00003 → NEW-00004 → NEW-00005
- **damage**: NEW-00003 → NEW-00001 → NEW-00005 → NEW-00004 → NEW-00002
- **deadline**: NEW-00005 → NEW-00004 → NEW-00003 → NEW-00001 → NEW-00002
- **fairness**: NEW-00005 → NEW-00004 → NEW-00003 → NEW-00001 → NEW-00002

Where the four disagreed most:

- `NEW-00001` was placed as high as 1 and as low as 4. This is where judgement was needed.
- `NEW-00002` was placed as high as 2 and as low as 5. This is where judgement was needed.
- `NEW-00005` was placed as high as 1 and as low as 5. This is where judgement was needed.

### Step 4  Read what the customer actually wrote

The four ways above only look at numbers, so they cannot tell a password reset apart from a break-in. Both look like one person with nothing failing. The words are the difference.

- `NEW-00001`: "our whole team is locked out. nobody can get in since about 6am. we have a client demo at 10 and I don't know what to tell them"
- `NEW-00002`: "I need to flag something. one of our customers has asked us to delete everything we hold on them. I believe there's a legal time limit on this and we're already a few days in"
- `NEW-00003`: "payments are failing at checkout. we've had maybe forty customers email us this morning saying their card was declined. our own test card fails too"
- `NEW-00004`: "there is a session logged in from a device we don't recognise and I can't work out how to end it. probably nothing but thought I should mention it"
- `NEW-00005`: "ABSOLUTELY UNACCEPTABLE. our dashboard chart is showing last month's figures. we pay you thousands every month and I expect better than this. I want someone to call me today"

### Step 5  The AI decides, and says why

**1. `NEW-00003`  Payments failing at checkout**  
Critical payment failures affecting thousands and blocking checkout force it to the top.

**2. `NEW-00001`  Team locked out**  
Team lockout blocks a client demo and affects hundreds, making it the second most urgent.

**3. `NEW-00004`  Unrecognized device session**  
Possible security breach triggers policy requiring at least top‑3 placement.

**4. `NEW-00002`  Customer data deletion request**  
Legal GDPR deletion request must not fall below fourth per policy.

**5. `NEW-00005`  Dashboard showing outdated data**  
Low‑impact dashboard bug with overdue SLA but the least business damage.


**The contradictions it spotted:**

- `NEW-00002` customer claimed High severity vs monitoring Low severity. It believed monitoring (and legal policy), because Monitoring reflects actual system impact and the legal policy overrides the customer's inflated severity.
- `NEW-00004` monitoring Low severity vs message suggesting a possible break‑in. It believed policy for suspected break‑in, because Monitoring cannot see security breaches, and the policy explicitly lifts such tickets.
- `NEW-00005` customer claimed Critical severity vs monitoring Low severity. It believed monitoring, because The issue affects few users and does not block work; the upset tone does not change the low technical impact.

**The trade-off it made:** We favoured immediate business impact and legal risk over pure revenue and fairness scores. This pushes a high‑paying Enterprise customer (NEW-00001) behind the payment failure, and a free‑plan security alert ahead of the legal request. The cost is a slight delay for the Enterprise demo and a perception of unfairness for the paying customer.

**The closest call:** Placing the security incident (NEW-00004) ahead of the legal GDPR request (NEW-00002) was hardest, because both have policy lifts and overdue status, and one could argue legal compliance should outrank a suspected breach.


**How it ranked the four ways of deciding:**

| Place | Way | Why here | What it gets wrong |
|---|---|---|---|
| 1 | damage | Business impact (users affected, work blocked) directly determines revenue loss and customer trust, which we prioritized. | It can undervalue high‑paying customers whose issues have lower immediate impact. |
| 2 | deadline | Legal and overdue tickets carry penalties and SLA breaches, so timing is the next priority. | Deadlines may push less damaging but time‑sensitive tickets ahead of higher‑impact problems. |
| 3 | money | Revenue is important but secondary to preventing large‑scale outages or legal breaches. | It can unfairly deprioritise free‑plan users with serious issues. |
| 4 | fairness | Ensuring equal treatment is valuable but was outweighed by impact, legal risk, and revenue considerations. | Relying on fairness alone could ignore critical business or compliance risks. |

### Step 6  Check the answer before anything happens

**Did every complaint come back, and were the written rules followed?**  
Yes. Nothing was dropped and no rule was broken.

**Were the reasons it gave actually true?**  
Yes. Every reason matched the numbers we hold.


**How solid was the answer?** One number was changed at a time and everything ranked again, to see which places were close calls.

| Ticket | How solid | Changes that move it |
|---|---|---|
| `NEW-00001` | solid | 0 of 7 |
| `NEW-00002` | solid | 0 of 6 |
| `NEW-00003` | fairly solid | 1 of 6 |
| `NEW-00004` | shaky | 3 of 6 |
| `NEW-00005` | fairly solid | 2 of 6 |

### Step 7  Hand them to a person

- `NEW-00003` goes to a person **now**
- `NEW-00001` goes to a person **next**
- `NEW-00004` goes to a person **next**  *(the numbers were not settled about this one)*
- `NEW-00002` goes to a person **queued**
- `NEW-00005` goes to a person **queued**

