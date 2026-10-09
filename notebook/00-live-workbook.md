# Engineering Workbook

> Build data capability by solving engineering problems.

This workbook is for an experienced software engineer who wants to develop practical data engineering and analytical skills, with a deliberate refresher in statistics and probability. Treat general software design, testing, and maintainability as existing strengths to apply, not subjects to relearn unless a concrete gap appears.

## How To Use This Workbook

Do not begin by studying every topic in advance.

Begin with the engineering challenge. Use the questions to scope a problem, then study only the knowledge needed to make progress.

The workflow:

```
1. Define the engineering problem

2. Identify questions and knowledge gaps

3. Learn and experiment as needed

4. Implement a useful solution

5. Check it with evidence

6. Reflect and try to transfer the learning
```

## Module Structure

Each module contains:

1. Engineering Challenge
2. Questions
3. Required Knowledge
4. Focused Reading
5. Experiments
6. Implementation
7. Engineering Review
8. Reflection

At the start of a module, mark each Required Knowledge item **F** (familiar), **R** (refresh), or **L** (learn). These are starting-point notes, not grades. Tick an item only when you can explain and apply it, and record evidence in the Engineering Review or Reflection.

There is no formal assessor. For each module, build your own confidence from several kinds of evidence: a working artefact, checks with known or synthetic examples, an explanation of assumptions and limitations, and a small attempt to apply the idea to a different dataset or source. If evidence is weak or contradictory, record the gap and revisit it rather than treating completion as proof of mastery.

## Module 1: Data Acquisition

### Engineering Challenge

"I want my personal data automatically collected."

Use these questions to define the challenge:

- Which data sources and types of personal data need to be collected?
- What does "automatically" mean for each source: how often should collection happen, and how much user effort is acceptable?
- How can each source be accessed, and what constraints could prevent or interrupt collection?
- What should the system deliver so collected data is ready for later use?

~~~

01 October 2026

* I already downloaded/exported the exercise data from my smart watch. I can periodically do this, manually; I am fine with it every now and then. Maybe every 2 weeks.
* Next, I was looking at FatSecret API. After signing up for dev account, I learned there is no direct way to pull user data. I reached out to support and they mentioned something like 3-legged OAuth.

* What does automatically mean? I want to pull json (or format to it if not available); I can write a Python script to do that and store them locally first. I will decide on db later; but most probably only local, i.e. SQLite
* Data Sources:
1. Smart watch exercise data (manual download/export)
2. FatSecret API (requires 3-legged OAuth)
3. Weighing scale. Idk yet but I found something via Bluetooth.

I am merely making assumptions on 3, but haven't done anything. I started with FatSecret API first.

02 October 2026
*  Bluetooth: I found Bleak library for Python

04 October 2026
* The bluetooth approach is limited to single data point - tapping live onto the scale.
* For historical data, I found an alternative to explore: the request-response cycle from the mobile app to Xiaomi cloud. No official endpoints publicly published though so this is some kind of "reverse-engineering" approach over my own wifi network.
* Alternatively, I looked into the mobile app and trying to find out if there's some accessible local db. This is much more elaborate than I thought and also manual - I don't like this. I'd rather jump straight on the cloud approach.

* This involves side quests though; learning about:
- Xiaomi ecosystem, its auth flow(s), API design, perhaps even its data modelling
- Using `HTTP Toolkit`; WireShark is much more low-level for this purpose?


Found endpoints:
- account.xiaomi.com

- sg.stream.api.mija.tech

- sg.core.api.io.mi.com
- sg.api.io.mi.com
- sg.home.mi.com
- api.account.xiaomi.com

05 October 2026

Paths explored:
* Support → no official API.
* BLE → only current/live measurements, not history.
* HTTP Toolkit → Android certificate wall.
* Existing Go implementation → authentication/config issues.
* Local log file → appears to be a binary log, not an obvious datastore.

06 October 2026
* Found a C#/MAUI mobile app on GitHub which I can extract the services from and compile as a CLI perhaps.

09 October 2026
* I messaged the author of the C#/MAUI mobile app the other day to ask whether he knows other auth methods; he pointed me to another repo - looks promising.
* The Xiaomi section makes me go in circles, haven't gotten past auth methods; this prevented me from building proper momentum on the whole project.
* Pivoted to first attempt on FatSecret API. I got a sample record for the month to date (in json). Good progress. Extracted it via Postman. Started working with Python implementation.

~~~

### Questions

~~~

* What is "3-legged OAuth" and how does it work?
- Found this link: https://platform.fatsecret.com/docs/guides/authentication/oauth1/three-legged

On Xiaomi:
1. Where does history come from?
- Local DB?
- Cloud endpoint?

2. How is authentication performed?
- Username/password
- OAuth
- Xiaomi SSO
- Device-bound tokens

3. Are requests signed?

~~~

### Required Knowledge

- [ ] I can describe the path from source through extraction and storage to data ready for analysis.
- [ ] I can investigate a source interface, its data contract, authentication, permissions, and access limits.
- [ ] I can distinguish full, incremental, and event-based collection, and choose an approach that fits the source.
- [ ] I can parse source formats while preserving raw values, timestamps, and source provenance needed for traceability.
- [ ] I can make collection repeatable through idempotency, retry, and recovery decisions appropriate to the source.
- [ ] I can detect and explain collection gaps, stale data, and partial failures.
- [ ] I can use representative source examples to check extraction and transformation behaviour.

### Focused Reading

Read only what addresses a current knowledge gap:

- What specific question do I need the material to answer?
- Which idea will I apply to the source or ingestion experiment?
- How will I check that I understood it rather than merely followed an example?

### Experiments

Build small experiments:

~~~

09 October 2026

I've been running circles looking for ways to build the auth for the Xiaomi cloud. I def don't want to do this manually. Heaps of reverse engineering I tried trying to intercept the traffic and understand the protocol, looked for endpoints, and explored various authentication methods.

~~~

### Implementation

Build:

~~~

09 October 2026

The bulk of my work from hitherto are mostly about exploring possible data acquisition from the 3 different sources. The FatSecret slice is where I started (auth) and now I successfully proven that I can pull my data from their API. I am now doing the Python implementation to pull and process the rest.


~~~

### Engineering Review

Answer:

~~~
1. What data sources and access methods does this module support, and what assumptions does each impose?

2. Where is the boundary between source-specific processing and the shared data service? Why is that boundary useful?

3. How are source data and normalised data represented? What information must be preserved for traceability or reprocessing?

4. What happens when a source is unavailable, returns malformed data, or provides the same data more than once?

5. Which alternatives did I consider, and what trade-offs led to this design?

6. What tests or real examples show that the integration works, including its failure paths?

7. How are credentials and personal data protected, and what would it take to add another source?
~~~

### Reflection

Record:

~~~
1. Which ingestion concept did I learn or refresh, and what artifact demonstrates that I can apply it?

2. Which test data or independent check gave me confidence in the result?

3. What failure mode or source limitation remains unresolved?

4. What would I change when integrating a source with a different access pattern?
~~~

## Module 2: Data Reliability

### Engineering Challenge

"My data exists, but can I trust it?"

Use these questions to define the challenge:

- What does "trustworthy" mean for the decisions or analyses this data will support?
- What kinds of errors, gaps, duplicates, or inconsistencies could occur in the collected data?
- Which quality rules determine whether a record is accepted, flagged, corrected, or rejected?
- How will I know whether a problem has been detected and whether the resulting data is fit for use?

~~~



~~~

### Questions

~~~



~~~

### Required Knowledge

- [ ] I can profile data for completeness, uniqueness, validity, consistency, and timeliness problems.
- [ ] I can define quality rules from the meaning, grain, and expected ranges of the data.
- [ ] I can design keys, relationships, constraints, and schema changes for the data's intended use.
- [ ] I can handle units, timestamps, time zones, and source provenance without hiding ambiguity.
- [ ] I can distinguish correcting, flagging, quarantining, and discarding records, and explain the consequences.
- [ ] I can preserve raw inputs and make transformations repeatable so corrected rules can be reapplied safely.
- [ ] I can test quality rules against valid, invalid, boundary, and conflicting examples.

### Focused Reading

Read only what addresses a current knowledge gap:

- Which quality, schema, or modelling decision am I trying to make?
- What rule or method from the material will I apply to my data?
- What example could show that the rule handles both valid data and a known problem?

### Experiments

Build small experiments:

~~~
Create a small dataset containing known quality problems. Apply the proposed rules, then check which records pass, fail, or need review.
~~~

### Implementation

Build:

~~~



~~~

### Engineering Review

Explain:

~~~
1. What does "reliable data" mean for this system, and which quality rules make that definition measurable?

2. How do I detect and handle missing, duplicated, malformed, conflicting, or out-of-range records?

3. How are timestamps, time zones, units, and source provenance checked and preserved?

4. Can I trace a cleaned value back to its source, correct a processing rule, and safely reprocess the data?

5. What evidence shows the checks catch real problems without rejecting valid data?

6. Which quality limitations remain, and how could they affect later analysis?
~~~

### Reflection

Record:

~~~
1. Which quality rules are supported by evidence about this source, and which are assumptions?

2. Can I trace a transformed value back to its input and reproduce the transformation?

3. Which unresolved data-quality issue could most distort a later analysis?

4. What would I check before trusting a new source with a different schema or measurement convention?
~~~

## Module 3: Data Analysis

### Engineering Challenge

"I have reliable data. What can I learn?"

Use these questions to define the challenge:

- What specific question or decision do I want the data analysis to inform?
- Which measures, groups, or time periods are needed to answer that question?
- What form of result would be useful and understandable to its intended reader?
- What should this analysis explicitly not claim to answer?

~~~



~~~

### Questions

~~~



~~~

### Required Knowledge

- [ ] I can use SQL or an equivalent tool to filter, join, group, and aggregate data for a defined question.
- [ ] I can state the grain of each dataset and avoid joins or aggregations that multiply or misalign records.
- [ ] I can explore an unfamiliar dataset with summaries, distributions, and visualisations before selecting an interpretation.
- [ ] I can analyse temporal data while accounting for missing intervals, irregular sampling, and changes in coverage.
- [ ] I can select a useful measure and chart, and describe what each does and does not show.
- [ ] I can make an analysis reproducible and distinguish observed results from explanations or recommendations.

### Focused Reading

Read only what addresses a current knowledge gap:

- Which analytical question or query am I trying to answer?
- What method, SQL pattern, or visualisation principle will I apply?
- How can I independently check the resulting query or interpretation?

### Experiments

Build small experiments:

~~~
Answer one analytical question with a small, inspectable dataset. Verify the filtering, joins, aggregation, and result with a hand-check or a second query.
~~~

### Implementation

Build:

~~~

~~~

### Engineering Review

Answer:

~~~
1. What specific question does the analysis answer, and what decision or understanding could it support?

2. What is the unit of analysis, and how were the data filtered, joined, or aggregated?

3. Can I reproduce the result from the stored data and documented steps?

4. What evidence supports the observed pattern, and could data quality or selection bias explain it?

5. Do the visualisations communicate the result clearly without implying more than the data shows?

6. What conclusions are justified, what remains uncertain, and what should I investigate next?
~~~

### Reflection

Record:

~~~
1. Can I reproduce the analysis from its inputs and documented steps?

2. Which result changed or challenged my initial expectation, and what could explain the difference?

3. What is the strongest alternative explanation for the pattern I observed?

4. What new analytical question can I now answer with the same approach?
~~~

## Module 4: Statistics and Probability

### Engineering Challenge

"How do I avoid misleading conclusions?"

Use these questions to define the challenge:

- What probability, quantity, difference, trend, or relationship am I trying to understand?
- What is the relevant population or process, and how were the observed data generated or sampled?
- How much uncertainty is acceptable for the decision or explanation I have in mind?
- What other factors, dependence over time, or data limitations could change the conclusion?
- What can the evidence support, and what would go beyond it?

~~~



~~~

### Questions

~~~



~~~

### Required Knowledge

- [ ] I can describe events, conditional probability, independence, and expected value, and recognise when an assumption such as independence is not plausible.
- [ ] I can apply Bayes' rule to update a probability in light of evidence and account for base rates.
- [ ] I can interpret common distributions and relate their parameters to real quantities and variability.
- [ ] I can explain sampling variability and why a sample statistic changes from sample to sample.
- [ ] I can explain the role and limits of the law of large numbers and the central limit theorem.
- [ ] I can estimate uncertainty and interpret confidence intervals without treating them as guarantees about an individual observation.
- [ ] I can interpret hypothesis tests and p-values without treating statistical significance as effect size, practical importance, or proof of a hypothesis.
- [ ] I can choose and interpret a basic comparison or regression model, and check whether its assumptions are reasonable.
- [ ] I can recognise confounding, selection effects, multiple comparisons, and the difference between association and causation.
- [ ] I can account for dependence and autocorrelation when observations are collected over time.

### Focused Reading

Read only what addresses a current knowledge gap:

- Which probability or statistical idea is necessary for the analysis?
- What assumptions and interpretation does the source explain?
- Can I restate the idea and verify it with a small calculation or simulation?

### Experiments

Build small experiments:

~~~
Use simulated or carefully chosen examples with known properties to compare intuition with calculation. Include at least one example involving sampling variability and one involving a time-dependent or confounded relationship.
~~~

### Implementation

Build:

~~~
Complete a reproducible statistical analysis of a focused question. Show the data, method, assumptions, uncertainty, and interpretation; include a simple independent or simulated check where possible.
~~~

### Engineering Review

Answer:

~~~
1. What is the estimand or probability I am trying to understand, and what population or process does it refer to?

2. How were the data generated, and are dependence, missingness, selection, or measurement error relevant?

3. Why is this method appropriate, and which assumptions matter most to its result?

4. Can I check the calculation against a known, simulated, or independently computed example?

5. How would a reasonable change in sample, assumptions, or method affect the conclusion?

6. Am I separating uncertainty, statistical evidence, practical importance, and causal claims?

7. What evidence would change my mind, and what remains uncertain?
~~~

### Reflection

Record:

~~~
1. Which statistical idea can I now explain in my own words and demonstrate with an example?

2. Which intuition did the calculation or simulation correct?

3. What assumption or limitation matters most for this conclusion?

4. Can I explain why the result does not support a stronger claim?
~~~

## Module 5: Machine Learning (Optional Extension)

### Engineering Challenge

"Can I learn useful patterns?"

Use these questions to define the challenge:

- What outcome or pattern might be predictable, and who would use that prediction?
- What is the prediction horizon, and which information would be available at prediction time?
- What action or understanding could a prediction support beyond a simple summary or rule?
- What evidence would show that the prediction is useful enough to justify its complexity and risks?

~~~



~~~

### Questions

~~~



~~~

### Required Knowledge

- [ ] I can turn a practical question into a prediction target, features, and a defined prediction horizon.
- [ ] I can prepare a training dataset and identify features that could leak future information.
- [ ] I can create an appropriate baseline and split data for evaluation, respecting time order when needed.
- [ ] I can select a model and evaluation metrics that fit the prediction task and its intended use.
- [ ] I can recognise overfitting and assess whether performance is likely to generalise.
- [ ] I can explain model limitations and the consequences of prediction errors.

### Focused Reading

Read only what addresses a current knowledge gap:

- What prediction or evaluation question am I trying to resolve?
- Which model or evaluation concept will I test?
- What baseline or held-out example will help me judge whether it is useful?

### Experiments

Build small experiments:

~~~

~~~

### Implementation

Build:

~~~

~~~

### Engineering Review

Answer:

~~~
1. What outcome am I predicting, for whom, and over what time horizon? Would the prediction be useful?

2. How did I define the target and features, and could any feature leak information unavailable at prediction time?

3. How does the model compare with a simple baseline using a metric tied to the intended use?

4. Was evaluation separated appropriately from training, and what does it show about generalisation?

5. Which groups, conditions, or future data might produce different performance?

6. What are the consequences of incorrect predictions, and what evidence would justify using this model?
~~~

### Reflection

Record:

~~~
1. Did a model add value beyond a simple summary or rule?

2. Can I explain its performance using the data split, baseline, and chosen metric?

3. Which limitation would stop me from using it for a real decision?

4. What further evidence would be needed before deployment?
~~~

## Module 6: AI Integration (Optional Extension)

### Engineering Challenge

"How can AI interact with my data?"

Use these questions to define the challenge:

- What user tasks should the AI help with, and who will use it?
- Why might an AI-based approach be more useful than a direct query, report, or deterministic rule?
- Which data and actions should the AI be allowed to access, and what must remain out of scope?
- What would a safe, useful response look like, and how should the system behave when it cannot provide one?

~~~



~~~

### Questions

~~~



~~~

### Required Knowledge

- [ ] I can distinguish tasks suited to an LLM from tasks better handled by queries, rules, or conventional software.
- [ ] I can design a controlled way for an AI component to access relevant structured data or tools.
- [ ] I can use clear instructions and structured outputs, then validate outputs before relying on them.
- [ ] I can ground responses in retrieved data and recognise the risk of unsupported or fabricated claims.
- [ ] I can evaluate AI behaviour with representative requests and failure cases.
- [ ] I can account for data permissions, privacy, and the cost and latency of AI calls.

### Focused Reading

Read only what addresses a current knowledge gap:

- What user task or AI failure mode am I trying to understand?
- Which design or evaluation technique will I apply?
- How will I check the AI response against data or an expected result?

### Experiments

Build small experiments:

~~~

~~~

### Implementation

Build:

~~~

~~~

### Engineering Review

Answer:

~~~
1. What user problem benefits from AI, and why is AI preferable to a simpler deterministic approach here?

2. What data or tools can the AI access, and how is its response grounded in that information?

3. How are sensitive data, permissions, and requests outside the system's scope handled?

4. How are outputs checked before they are shown or used, and what happens when the AI is uncertain or wrong?

5. How will I evaluate usefulness and reliability using representative questions and failure cases?

6. What are the latency, cost, and operational trade-offs, and what risks remain?
~~~

### Reflection

Record:

~~~
1. Which task was improved by AI, and how did I establish that it was actually useful?

2. What failure example exposed a weakness in the approach?

3. What controls limit the impact of an incorrect or unsupported response?

4. When should this task use a query, rule, or conventional software instead?
~~~


## Final Engineering Review

The core project is complete when I can:

### Explain

The data flow, analytical model, and key assumptions clearly, using a concise diagram or written explanation.

### Build

A small pipeline and reproducible analysis for a new source or dataset using the same principles.

### Review

Data quality, statistical assumptions, uncertainty, and engineering trade-offs using evidence rather than confidence alone.

### Transfer

The approach to a different kind of dataset and identify what must change.

### Explain to myself

The important concepts without notes, for example by recording a short explanation, writing a worked example, or answering a new set of questions.

Machine Learning and AI Integration are optional extensions, not prerequisites for completing the core data and statistics learning path.


## Engineering Journal Requirement

For each module, record:

~~~
1. What did I already know, refresh, or need to learn?

2. What artifact or analysis did I produce?

3. What checks, known examples, or independent calculations support its correctness?

4. What can I explain now, and what assumptions or limitations remain?

5. Can I apply the idea to a different dataset or problem? What happened?

6. What is my next knowledge gap?
~~~



## Final Principle

Do not measure progress by completed topics or confidence alone.

Measure progress by problems solved, evidence examined, and engineering judgement gained.