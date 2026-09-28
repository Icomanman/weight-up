# Project Syllabus

> Build a real system. Learn through the problems it creates.

---

## Project Mission

Build a personal health data platform that collects, stores, validates, and analyses personal data.

The system will integrate:

- Weight measurements
- Nutrition data
- Activity data
- Exercise data
- Other personal data sources over time

The learner is an experienced software engineer. The project should build on existing engineering skills rather than spend time re-teaching general software design, testing, and modularity.

The health domain is only the vehicle.

The core objective is to develop transferable capability in:

- Data engineering
- Database design
- Analytical workflows
- Statistics and probability, including a practical refresher

Machine learning and AI are optional extensions, not prerequisites for completing the core learning path.

The final outcome is the ability to design data workflows, analyse data reproducibly, reason about uncertainty, and explain the evidence and limitations.

---

## Learning Philosophy

This project follows an engineering apprenticeship model.

Learning happens through the following loop:
```
1. Build

2. Encounter Real Problem

3. Identify Knowledge Gap

4. Study Relevant Concepts

5. Apply Solution

6. Reflect

7. Explain and transfer
```

The order matters.

The project creates the problems.

The problems determine what needs to be learned.

There is no formal assessor. Learning is self-directed: retain artefacts, check work against known or simulated examples, explain assumptions and limitations, and try the method on a different dataset. Self-confidence alone is not evidence of correctness.

---

## Why This Approach

Real engineering rarely begins with:

"I want to learn ETL."

It begins with:

"I need to combine three unreliable data sources into one system."

The engineering problem creates the need for knowledge.

This project intentionally follows that process.

---

## Project Journey

The project progresses through engineering capability stages.

---

### Phase 1: Build the Data Foundation (Core)

#### Engineering Challenge

"I have multiple sources of personal data. How do I collect them automatically?"

Sources:

- Xiaomi weighing scale
- Samsung smartwatch
- FatSecret nutrition data

---

#### Problems Encountered

Examples:

- How do the available APIs, exports, or device interfaces work?
- How do I store raw data?
- How do I handle failures?
- How do I avoid duplicate imports?
- How do I know whether collection is complete and current?

---

#### Concepts Learned

- Source contracts and access constraints
- Batch and incremental ingestion
- Raw data preservation and provenance
- Idempotency, recovery, and observability

---

#### Deliverable

A repeatable ingestion workflow for the selected sources, with source-access constraints and any manual steps documented.

---

### Phase 2: Build Data Reliability and Models (Core)

#### Engineering Challenge

"I have collected data. How do I trust it?"

---

#### Problems Encountered

Examples:

- Missing data
- Duplicate records
- Different formats
- Incorrect timestamps
- Unit mismatches
- Schema changes
- Ambiguous records and conflicting measurements

---

#### Concepts Learned

- Data quality
- Data validation
- Repeatable data transformation
- Database modelling
- Schema design
- Units, timestamps, and provenance

---

#### Deliverable

A data model and repeatable validation workflow with documented quality rules and known limitations.

---

### Phase 3: Analyse the Data (Core)

#### Engineering Challenge

"I have data. What does it actually tell me?"

---

#### Problems Encountered

Examples:

- How should data be explored?
- Which patterns matter?
- How do I avoid misleading conclusions?
- Are joins and aggregations preserving the intended unit of analysis?

---

#### Concepts Learned

- Exploratory data analysis
- Visualisation
- SQL and analytical queries
- Reproducible analysis
- Analytical reasoning

---

#### Deliverable

An analytics layer.

---

### Phase 4: Reason About Probability and Uncertainty (Core)

#### Engineering Challenge

"How strong is the evidence, and what uncertainty remains?"

#### Problems Encountered

Examples:

- How much would a result vary if I collected another sample?
- What do probability, independence, and conditional probability mean for this data?
- What does a confidence interval or p-value actually say?
- How can confounding or temporal dependence mislead me?
- Which claims are justified, and which would imply causation without evidence?

#### Concepts Learned

- Probability and conditional probability
- Bayes' rule and base rates
- Distributions and expected value
- Sampling variability
- Confidence intervals and hypothesis tests
- Regression, confounding, and limits of inference
- Time dependence and autocorrelation

#### Deliverable

A reproducible analysis that explains its assumptions, uncertainty, and limits, checked against a known or simulated example.

---

### Phase 5: Learn From Data (Optional Extension)

#### Engineering Challenge

"Can I identify patterns and make predictions?"

---

#### Problems Encountered

Examples:

- What should be predicted?
- Which features matter?
- How do I evaluate success?

---

#### Concepts Learned

- Feature engineering
- Machine learning workflow
- Model evaluation
- Prediction

---

#### Deliverable

Predictive experiments.

---

### Phase 6: Add Intelligence (Optional Extension)

#### Engineering Challenge

"How can AI interact with my data?"

---

#### Problems Encountered

Examples:

- How does an AI system access structured information?
- When should AI be used?
- How do we avoid hallucination?

---

#### Concepts Learned

- LLM applications
- Retrieval
- Structured outputs
- AI system architecture

---

#### Deliverable

An AI interface over the platform.

---

## Learning Outcomes

By completing the project, I should be able to:

### Design Systems

I can design an end-to-end software architecture.

#### Evidence

- I can explain every component.
- I can justify boundaries.
- I can discuss trade-offs.

---

### Build Data Pipelines

I can create reliable ingestion systems.

#### Evidence

- I can add new data sources.
- I understand failure modes.
- I can maintain data quality.

---

### Work With Data

I can investigate unfamiliar datasets.

#### Evidence

- I can clean data.
- I can visualise patterns.
- I can explain conclusions.

---

### Apply Statistics

I can reason about probability, sampling variability, uncertainty, and limitations of inference.

#### Evidence

- I understand limitations of analysis.
- I avoid confusing correlation and causation.

---

### Apply Machine Learning

Optional extension:

I can build and evaluate models.

#### Evidence

- I can define prediction problems.
- I can select appropriate approaches.
- I can critique results.

---

### Build AI Systems

Optional extension:

I can integrate AI into software systems.

#### Evidence

- I understand where AI adds value.
- I can design AI workflows.

---

## Core Success Criteria

Use these as evidence prompts, not a formal grading rubric. The core project succeeds when:

### Technical

- Data collection is automated.
- Data quality rules and known limitations are documented and checked.
- The data model supports the intended analytical questions.
- At least one analysis can be reproduced from documented inputs and steps.
- Statistical reasoning is checked against known, simulated, or independently computed examples.
- Conclusions describe uncertainty and avoid claims the evidence cannot support.

---

### Engineering

I can explain:

- How data moves through the system and why the main boundaries exist.
- Why alternatives were rejected and what trade-offs were made.
- What assumptions, quality issues, and limitations remain.
- How I checked the results and what evidence would change my conclusion.

---

### Transferability

I can reuse the same principles for:

- Structural engineering systems
- IoT platforms
- Manufacturing systems
- Financial analytics

---

## Scope Boundaries

This project does NOT aim to become:

- A medical application
- A nutrition science project
- A deep learning research project
- A commercial health product

Those are separate projects.

---

## Guiding Principle

> The project is the classroom.
>
> Problems create learning.
>
> Evidence supports capability.
>
> Reflection creates expertise.