# Reflection on the Iterative Development of the Life Project Prompt Design  
**(Grounded in Classification Outcomes)**

## Introduction
This document summarizes the step-by-step evolution of the prompt design used in the Life Project life-goal classification system. Each version (V1–V6) was not designed theoretically, but **driven by real model behavior** observed in the classification results. The goal was to improve accuracy, consistency, cultural understanding, and transparency.

---

## Phase 1 — Minimal Viable Prompt (V1)

### Initial Goal
Run the system successfully with the simplest possible prompt:
- Define the model’s role
- Ask for a category only
- Test feasibility

### Observed Outcomes
- ✅ The model returned a category for each goal.
- ❌ High misclassification, especially:
  - Broad overuse of **WEC** and **Oth**
  - Confusion between housing, finance, and career
- ❌ No multi-label assignments
- ❌ Cultural expressions were often misunderstood

### Key Insight
A minimal prompt works functionally but **not reliably**. More structure was needed.

---

## Phase 2 — Adding Structure and Instructions (V2)

### What Changed
The prompt added:
- Background
- Task description
- Code instructions

### Observed Improvements
- ✅ Clearer category boundaries
- ✅ Fewer irrelevant labels
- ✅ More consistency across similar goals

### Remaining Problems
- ❌ Model still struggled with ambiguous goals
- ❌ Multi-coding rarely applied
- ❌ No explanation for decisions

### Key Insight
Structure helped, but **lack of reasoning made errors opaque**.

---

## Phase 3 — Introducing Reasoning (V3)

### What Changed
The model was asked to:
- Provide both **category + reasoning**

### Impact on Results
- ✅ Reasoning exposed misunderstandings, such as:
  - MAR interpreted as “marriage”
- ✅ Revealed when multiple domains were recognized but only one category was chosen

### Why This Mattered
For the first time, errors became **diagnosable**, enabling:
- Codebook improvements
- Targeted prompt revisions

### Key Insight
Reasoning transformed the system from a black box to a **transparent decision process**.

---

## Phase 4 — Adding Language Context & Heuristics (V4)

### Motivation
Classifications in Brazilian Portuguese revealed:
- Cultural misinterpretations
- Travel vs relocation confusion
- Misunderstanding of regional expressions

### What Changed
Added:
- Language hints
- Heuristic guidance for overlapping domains

### Observed Improvements
- ✅ Better handling of:
  - **Tra** vs **MAR**
  - **EFT** vs **WEC**
- ✅ More accurate multi-coding in overlapping domains

### Remaining Gaps
- Housing vs well-being (`HOU` vs `HQL`)
- Career vs finance (`WEC` vs `FS`)

### Key Insight
Context matters — but heuristics alone **couldn’t fix systematic errors**.

---

## Phase 5 — Introducing Hard Rules (V5)

### What Changed
Hard rules were added to correct recurring misclassifications, including:
- Study abroad → **MAR + WEC**
- NGO work → **CI + WEC**, not CI alone
- Financial goals misclassified into WEC

### Impact on Results
- ✅ Multi-coding applied more reliably
- ✅ Oth usage dropped
- ✅ Recurring errors disappeared

### Key Insight
**hard rules enforce**.

---

## Phase 6 — Streamlining and Expanding Categories (V6)

### Data-Driven Motivation
Results showed:
- “Oth” became a catch-all category
- Death-related and pet-related goals appeared frequently

### What Changed
Two new categories were introduced:
- **dth** (death-related)
- **pet** (pet-related)

Soft rules were removed.

### Impact
- ✅ Reduced misclassification into Oth
- ✅ Clearer semantic boundaries
- ✅ More interpretable results

### Key Insight
Codebooks must evolve with real data. Classification outcomes should drive category updates.

---

## Overall Evolution Summary

| Prompt Phase |       Problem Observed     |          Solution Added         |
|--------------|----------------------------|---------------------------------|
| V1 → V2      | Unstable categories        | Structure & instructions        |
| V2 → V3      | No transparency            | Reasoning                       |
| V3 → V4      | Cultural misclassification | Language hints & heuristics     |
| V4 → V5      | Repeated systematic errors | Hard rules                      |
| V5 → V6      | Category overload (“Oth”)  | New categories & simplification |

---

## Final Reflection
The prompt journey moved from a simple functional design to a **research-grade annotation framework**. The key principle throughout was:

> Every prompt change was driven by real classification outcomes — not intuition.

The final system is:
- More accurate
- More explainable
- More culturally aware
- More rule-based
- More scalable

---


