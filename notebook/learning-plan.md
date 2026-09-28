# Learning Plan

## Project-Based Learning Roadmap

> **Primary Objective**
>
> Build on 5+ years of software engineering experience to develop practical data engineering,
> analytical, statistical, and probabilistic reasoning through a real-world personal dataset.
>
> The health insights are secondary; this is a self-study project, not a formally assessed course.
>
> The primary deliverable is demonstrated data capability, supported by working artefacts,
> independent checks, clear explanations, and transfer to a different dataset.

---

## Overall Learning Outcomes

By completing this project, I should be able to confidently:

### Systems Design

- Design an end-to-end data platform from scratch.
- Explain why each architectural component exists.
- Evaluate trade-offs between different architectural approaches.
- Add a new data source with minimal changes to the existing system.

#### Evidence

I can draw the data flow and explain its boundaries, trade-offs, and failure modes without relying on undocumented assumptions.

---

### Data Engineering

- Design reliable ETL pipelines.
- Normalise heterogeneous datasets.
- Handle schema evolution.
- Detect and recover from bad data.
- Build repeatable ingestion workflows.

#### Evidence

I can integrate a different data source by investigating its contract, mapping its data, testing its failure modes, and explaining the changes required.

---

### Database Design

- Design schemas for analytical workloads.
- Choose appropriate keys and relationships.
- Optimise queries.
- Understand normalisation versus denormalisation.

#### Evidence

I can justify every table and relationship in my schema.

---

### Data Analysis

- Explore unknown datasets.
- Identify useful questions.
- Produce reproducible analyses.
- Communicate findings visually.

#### Evidence

I can answer questions using data instead of intuition.

---

### Statistics and Probability

- Explain probability, conditional probability, independence, and expected value.
- Apply Bayes' rule and account for base rates when interpreting evidence.
- Understand distributions, sampling variability, and how sample size affects uncertainty.
- Interpret confidence intervals, hypothesis tests, and regression results appropriately.
- Recognise confounding, selection effects, temporal dependence, and the limits of causal claims.

#### Evidence

I can explain a statistical conclusion in context, check it against a known or simulated example, and identify assumptions that could change it.

---

### Time-Series Analysis

- Recognise trends.
- Identify seasonality.
- Engineer lag-based features.
- Handle temporal dependencies.

#### Evidence

I naturally think about time when designing analyses instead of treating every observation independently.

---

### Machine Learning

Optional extension:

- Formulate prediction problems.
- Build training datasets.
- Engineer meaningful features.
- Evaluate models appropriately.
- Explain model limitations.

#### Evidence

I know why one model performs better than another rather than simply accepting benchmark scores.

---

### AI Engineering

Optional extension:

- Design AI applications around structured data.
- Build LLM-assisted workflows.
- Use structured outputs.
- Integrate retrieval where appropriate.
- Understand when AI adds value—and when it does not.

#### Evidence

I can clearly explain why a particular AI component exists and what problem it solves.

---

### Software Engineering

Apply existing software engineering strengths where they support the data work; revisit these topics only when the project exposes a specific gap.

---

### Engineering Mindset

- Break large problems into manageable components.
- Learn unfamiliar technologies independently.
- Read documentation efficiently.
- Make informed trade-offs instead of chasing the "perfect" solution.

#### Evidence

I am comfortable building systems using technologies I have never used before.

---

## Success Criteria

Use these criteria for self-review, not as a formal grading rubric. The core path is data acquisition, data reliability and modelling, analysis, and statistics and probability. Machine learning and AI are optional extensions.

### Technical

- [ ] Selected sources can be collected repeatably within their access constraints, with manual steps documented.
- [ ] The data model and analysis can be recreated from documented raw inputs and processing steps.
- [ ] New data sources are straightforward to integrate.
- [ ] Pipelines are reliable and repeatable.
- [ ] Data quality issues are detected automatically.
- [ ] The database supports intended analytical questions without unnecessary complexity.
- [ ] At least one analytical result can be reproduced from documented inputs and steps.
- [ ] Statistical conclusions include appropriate checks, assumptions, and uncertainty.

Optional extensions:

- [ ] The dashboard updates automatically.
- [ ] A predictive model is compared with a simple baseline and evaluated without data leakage.
- [ ] An AI feature uses controlled access to structured data and is checked against representative failure cases.

---

### Knowledge

I can explain, from memory:

- [ ] ETL vs ELT
- [ ] Data normalisation
- [ ] Data grain, provenance, and idempotent ingestion
- [ ] Data quality dimensions and schema evolution
- [ ] Probability, conditional probability, Bayes' rule, and independence
- [ ] Sampling variability and common distributions
- [ ] Confidence intervals and hypothesis tests
- [ ] Confounding, temporal dependence, and correlation vs causation
- [ ] Time-series analysis

Optional extensions:

- [ ] Feature engineering, model evaluation, overfitting, and data leakage
- [ ] Precision, recall, and accuracy
- [ ] Why an LLM is not a machine learning model in the traditional sense

---

### Practical Skills

Without following a tutorial, I can:

- [ ] Import a new dataset.
- [ ] Design a relational schema.
- [ ] Clean inconsistent data.
- [ ] Perform exploratory data analysis.
- [ ] Build visualisations.
- [ ] Query and aggregate data without changing its intended grain.
- [ ] Analyse uncertainty using a worked or simulated example.
- [ ] Reproduce and critique an analytical result.

Optional extensions:

- [ ] Train and evaluate a predictive model.
- [ ] Build an AI assistant over the dataset with explicit data-access boundaries.

---

### Communication

I can explain this project to:

#### A non-technical person

In under five minutes.

#### A software engineer

Including the architecture and engineering trade-offs.

#### A data scientist

Including the question, data-generating process, statistical assumptions, uncertainty, and limits of inference.

#### An engineer working with data

Including why data engineering, statistical analysis, and (if used) machine learning or LLMs each play different roles.

---

## Final Reflection

The project is complete when I no longer think of it as "a health tracker."

Instead, I recognise it as a complete software system that happens to use health data.

If someone replaced the health data with financial transactions, IoT sensor readings, manufacturing telemetry, or structural monitoring data, I should know exactly how to adapt the architecture.

That transferability—not the health insights—is the real measure of success.

Because there is no external assessor, use more than self-confidence to judge progress: retain working artefacts, check calculations against known or simulated cases, document assumptions and limitations, and attempt at least one small transfer task using a different dataset.