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

