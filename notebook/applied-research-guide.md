# Applied Research Guide

> Explore how an established idea appears in everyday data—and what imperfect measurements let us conclude.

## Working Theme

Energy balance is established knowledge: changes in stored body energy reflect the balance between energy intake and energy expenditure. The practical challenge in this project is not to rediscover that principle. It is to examine how it appears, or fails to appear clearly, when a person tries to observe it through ordinary tracking tools:

- a scale that records body weight;
- a food log that records estimated intake from entered items;
- a smartwatch that estimates activity or energy expenditure.

These instruments do not directly measure the full energy balance. Their values have different meanings, error sources, and gaps. Body weight also changes in the short term for reasons that do not map neatly onto changes in body fat. The project is about the **distance between a useful model and the imperfect measurements available in everyday life**.

## A Proposal to Start From

### Working title

**Energy Balance in Everyday Data: What My Scale, Food Log, and Smartwatch Can—and Cannot—Show**

### Practical problem

People encounter calorie and weight numbers in apps and devices, but those numbers can look more exact than the underlying measurements justify. How can someone interpret ordinary tracking data without either dismissing useful information or over-trusting estimates?

### Aim

To examine how the energy-balance model can be interpreted using my real-world weight, food-log, and smartwatch records, and how source limitations, missing data, and measurement variability affect the conclusions.

### Primary research question

> How does the established energy-balance model appear in my real-world weight, food-log, and smartwatch data over time, and how do the limitations of those measurements shape what I can conclude?

### Supporting questions

- What trends and patterns are visible when the records are aligned over time?
- How complete and consistent are the records, and what does each source actually measure or estimate?
- Do conclusions change when I use longer-term summaries rather than daily values, or when I account for incomplete periods?
- Which apparent disagreements between sources can be explained by measurement limitations, timing, or missingness?
- What practical interpretation of the data is useful for my own decisions, without treating estimates as exact?

These questions can be narrowed once the data coverage and relevant literature are understood.

### Starting expectation

The broad expectation is that longer-term weight change may be broadly compatible with patterns in recorded intake and estimated expenditure, while daily numbers may not line up cleanly. This is an expectation to examine, not a result to assume. The records may be incomplete, the estimates may be biased, and the observed pattern may not support a clear interpretation.

## What This Project Can Contribute

The basic energy-balance principle is not the novelty. A useful applied contribution could be a transparent, data-backed case study showing:

- what everyday tracking sources actually provide;
- how a familiar model meets incomplete and imprecise measurements;
- how choices such as aggregation and data-quality rules affect the apparent story;
- what conclusions remain reasonable—and which tempting conclusions are not supported;
- how a person can use the numbers without treating every displayed calorie as ground truth.

The strength of the work is not that one person's data represents everyone. It is that readers can see the data, the measurement context, the reasoning, and the limits together. Existing research can help explain which parts may transfer to other people or devices; it does not make this personal case statistically representative.

Do not claim that no similar personal-data story exists until a focused search has checked that. A more defensible point of difference may be the particular combination of data sources and the transparent account of their limitations.

## Keep the Concepts Distinct

Use these terms precisely:

- **Behavioural consistency:** how regularly a behaviour or logging practice occurs.
- **Measurement consistency / repeatability:** whether repeated measurements under similar conditions agree.
- **Precision:** the degree of agreement among repeated measurements.
- **Accuracy:** how close a measurement is to an appropriate reference or true value.
- **Completeness:** whether the expected records are present.
- **Trend:** a pattern over time, which may be more useful than a single reading but still depends on data quality and the chosen summary.

Consistency of behaviour, consistency of measurement, and measurement accuracy are not interchangeable. If investigating one of them, define how it will be represented in the data. Do not make the broad claim that “consistency and precision matter more” unless the project has a clear comparison and outcome that could support it.

## Research Workflow

### 1. Establish the practical question

Begin with the problem of interpreting numbers, not with a promise to confirm a conclusion:

> I want to understand what my tracking data can tell me about energy balance and weight change, and where the measurements make that interpretation uncertain.

Write down:

- What would I like to understand or decide?
- Which numbers do I currently rely on?
- What assumptions do I make about those numbers?
- What finding would surprise me or change my interpretation?

### 2. Review relevant literature before the main analysis

Use an initial literature review to understand the model, the instruments, and the interpretation problem. Search separately for:

- energy balance and dynamic changes in body weight;
- consumer wearable estimates of energy expenditure and their validation;
- dietary self-report or food logging, including omissions and estimation error;
- self-weighing, short-term weight variability, and trend interpretation;
- practical use of self-monitoring, if it informs the intended audience or decision.

For each useful source, record its question, population, measurement methods, comparison standard (if any), main findings, limitations, and relevance to this project. Check whether the study concerns the same kind of device, metric, and use. Evidence about step counts, for example, does not automatically validate calorie expenditure estimates.

The literature should inform the question and analysis, not predetermine the result. After seeing the findings, a targeted follow-up search can help interpret unexpected patterns; label explanations developed afterwards as exploratory.

### 3. Define the case and its boundaries

Specify before analysis:

- the person and data sources covered;
- the dates included and why;
- the unit and meaning of each record;
- what counts as a complete day or period, if relevant;
- the primary outcome or trend to describe;
- the comparisons planned;
- what the project will not claim.

This project can describe patterns in one person's observational records. It cannot isolate the causal effect of a behaviour, determine an exact energy deficit from consumer-device outputs, or establish what will happen to an average person.

### 4. Understand the measurement chain

For each source, document:

| Source | What is recorded | What it does not establish by itself |
|---|---|---|
| Scale | A body-weight reading at a time and under particular conditions | Body-fat change or the cause of a weight change |
| Food log | Items entered and their associated intake estimates | Complete or exact energy intake |
| Smartwatch | Device-specific activity or energy estimates | Exact total energy expenditure or energy balance |

Confirm the actual fields, units, timestamps, and semantics in your exports; do not assume a field means what its display label suggests. Preserve raw values and provenance. An absent record is not automatically zero, and a recorded value is not automatically accurate or complete.

### 5. Write a simple analysis plan

Before examining results in detail, record:

- the main question and descriptive measure;
- how data from different sources will be aligned in time;
- how trends will be summarised;
- how gaps, duplicates, and incomplete periods will be handled;
- which comparisons are primary and which are exploratory;
- what plausible alternative explanations could affect interpretation;
- what result would weaken your starting expectation.

Prefer a small number of interpretable summaries. Daily values can be useful for inspecting variability and coverage; longer-term summaries can help describe trends. Neither should be presented as a direct measurement of daily energy balance.

### 6. Check the data before interpreting it

Inspect:

- coverage by source and date;
- missing, duplicated, malformed, or changing records;
- units, time zones, and timestamp alignment;
- whether records represent daily totals, events, or estimates;
- whether periods being compared have comparable coverage.

Keep the raw data distinct from cleaned and aggregated data. Make transformations reproducible so that a different quality rule or summary can be checked later.

### 7. Analyse patterns and sensitivity

Describe the data before offering an explanation. Plot or summarise the aligned time series, then ask:

- What changes are visible, and over what time scale?
- Do the sources tell a consistent story, or do they disagree?
- Does the interpretation change with another reasonable aggregation or inclusion rule?
- Could missing entries, measurement error, timing, or normal weight variation explain the pattern?
- Which conclusions are robust to these reasonable choices, and which are fragile?

Separate three layers:

| Layer | Example |
|---|---|
| Observation | The recorded weight trend declined over this period. |
| Interpretation | This is compatible with weight loss, but the records do not identify the precise energy deficit or explain all short-term variation. |
| Practical implication | For my own review, I will use the longer-term weight trend and treat device calorie estimates as uncertain context. |

Association between recorded intake, estimated expenditure, and weight change is not proof of causation. A simple subtraction of logged food calories and smartwatch calories should not be treated as a validated measure of energy balance.

### 8. Compare with the literature

Use prior studies to assess whether your observations are plausible and what might limit transfer:

- Were similar metrics and devices studied?
- Were those measures compared with a suitable reference?
- Does the study support the measurement, the interpretation, or a behavioural recommendation? These are separate claims.
- Could differences in population, device version, protocol, or data completeness explain different results?

The literature can provide broader context. Your case can illustrate how the measurement problem played out for you. Keep those evidence roles distinct.

### 9. State a bounded conclusion

Report what the evidence supports at each level:

1. **Observed in this case:** the patterns and data-quality facts.
2. **Interpretation:** how those observations fit, or fail to fit, the energy-balance model, given measurement uncertainty.
3. **Practical lesson:** what you would do differently when interpreting your own tracking data.
4. **Broader context:** what relevant literature suggests, with its population and device limitations.
5. **Unresolved:** what the available data cannot establish.

If the result aligns with expectations, explain how strongly and what alternative explanations remain. If it does not align, do not force a reconciliation: investigate the records, methods, and possible explanations, then report the uncertainty.

## Objectivity in a Personal Project

Having a personal stake does not prevent useful research. Make the reasoning inspectable:

**Before analysis**

- Write down your expectation and why you hold it.
- Record at least one plausible alternative explanation.
- State what result would make you reconsider.
- Decide which analyses are planned and which may be exploratory.

**During analysis**

- Preserve source data and document transformations.
- Record exclusions, assumptions, and changes to the plan.
- Include discordant results and inconvenient data-quality findings.
- Distinguish measurements, estimates, interpretations, and decisions.

**When writing**

- Separate what your records show from what you infer.
- Compare fairly with relevant and conflicting literature.
- Do not strengthen a claim merely to make the story more compelling.

## Article Structure

A practical article or report could follow this narrative:

1. **The familiar model:** energy balance is well established.
2. **The everyday problem:** tracking tools offer numbers, but their meaning and quality differ.
3. **The question:** what can this person's real-world records show about the model?
4. **The evidence:** sources, dates, coverage, data-quality checks, and analysis choices.
5. **The result:** what patterns appeared, including conflicts and gaps.
6. **The interpretation:** how measurement limitations shape the apparent relationship.
7. **The practical takeaway:** how to use such numbers without over-trusting or dismissing them.
8. **The boundary:** what this case cannot say about causation or other people.

The story should be determined by the results. It may support the starting expectation, complicate it, or leave the relationship too uncertain to interpret. Each of those can produce a useful account if the method and limits are clear.

## One-Page Working Proposal

Complete this before the main analysis and revise it when new evidence warrants:

```text
Working title:

Practical problem:

Aim:

Primary research question:

Supporting questions:

Starting expectation (not a required conclusion):

Data sources, fields, units, and what they measure:

Dates and inclusion rules:

Primary summaries and planned comparisons:

Data-quality checks:

Relevant literature and search terms:

Alternative explanations:

What evidence would change my interpretation:

Privacy and data-handling steps:

Claims this case cannot support:
```

## Completion Criteria

The work is ready to communicate when:

- the question and scope are explicit;
- each source's meaning and limitations are described;
- data coverage and analysis choices are reproducible;
- results are separated from interpretation and practical advice;
- relevant literature is used as context rather than confirmation;
- uncertainty and alternative explanations are reported;
- readers can distinguish this personal case from broader evidence.

This guide complements the [live workbook](./00-live-workbook.md), especially its modules on data reliability, analysis, and statistics. It is a working method: update the question as the evidence clarifies what can responsibly be answered.
