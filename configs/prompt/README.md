# Prompt Guide
This directory contains all prompt components used for life-goal classification in the Life Project system.  
A final prompt is created by **concatenating specific text files** in a fixed order.
Each version (V1–V6) represents a different combination of components.

## Folder Structure
```bash
prompt/
  codebook/
    codebook_en.txt
  language_hint/
    pt-BR.txt
    zh-TW.txt
  taskset/
    role.txt
    background.txt
    task_intr.txt
    code_intr.txt
    reasoning.txt
    heuristics.txt
    hard_rules.txt
    output_1.txt
    output_2.txt
```
- **taskset/** contains all building blocks except language and codebook
- **language_hint/** is optional (used only in V4–V6)
- **codebook/** is always included

All files are plain text.

## Prompt Component Definitions
| Component       | Meaning                      |
| --------------- | ---------------------------- |
| `language_hint` | Language / cultural guidance |
| `role`          | LLM role definition          |
| `background`    | Context of the task          |
| `task_intr`     | Task introduction            |
| `code_intr`     | Coding instructions          |
| `reasoning`     | Reasoning guidance           |
| `heuristics`    | Soft rules                   |
| `hard_rules`    | Hard rules                   |
| `output_1`      | Basic output format          |
| `output_2`      | Extended output format       |
| `codebook_en`   | Category definitions         |


## Version Statement
V1：role + +output_1 + codebook_en 
V2：role + background + task_intr + code_intr + output_1 + codebook_en 
V3: role + background + task_intr + reasoning + code_intr + output_2 + codebook_en 
V4: language_hint + role + background + task_intr + reasoning + code_intr + heuristics + output_2 + codebook_en 
V5: language_hint + role + background + task_intr + reasoning + code_intr + hard_rule + heuristics + output_2 + codebook_en 
V6: language_hint + role + background + task_intr + reasoning + code_intr + hard_rule + output_2 + codebook_en 

Each version is a fixed concatenation of components:
| Version | Role |       Output Format     | codebook | language hint | background | task intro | code intro | Reasoning | Soft Rules | Hard Rules |
|---------|------|-------------------------|----------|---------------|------------|------------|------------|-----------|------------|------------|
| **V1**  | Yes  | only `category`         |   Yes    |      No       |     No     |     No     |     No     |    No     |     No     |     No     |
| **V2**  | Yes  | only `category`         |   Yes    |      No       |     Yes    |     Yes    |     Yes    |    No     |     No     |     No     |
| **V3**  | Yes  | `category` + `reasoing` |   Yes    |      No       |     Yes    |     Yes    |     Yes    |    Yes    |     No     |     No     |
| **V4**  | Yes  | `category` + `reasoing` |   Yes    |      Yes      |     Yes    |     Yes    |     Yes    |    Yes    |     Yes    |     No     |
| **V5**  | Yes  | `category` + `reasoing` |   Yes    |      Yes      |     Yes    |     Yes    |     Yes    |    Yes    |     Yes    |     Yes    |
| **V6**  | Yes  | `category` + `reasoing` |   Yes    |      Yes      |     Yes    |     Yes    |     Yes    |    Yes    |     No     |     Yes    |

**Notes:**
- `language_hint` only appears in V4–V6
- `codebook_en` is always added last
- `output_1` is used in V1–V2, `output_2` in V3–V6

## How Prompts Are Built
- Prompts are assembled automatically by code:
  1. Identify version (V1–V6)
  2. Load the required components in order
  3. Concatenate them into a single system prompt
  4. Send the system prompt to the model

- User prompts are built separately during classification.

## Updating or Adding Versions
New components can be added by creating new text files in the `taskset/` folder and updating the version mapping accordingly in `prompt_builder`.

```bush
VERSION_MAP = {
  # Future versions can be added here
  "V7" : ["language_hint", "role", "background", "task_intr", "reasoning", "code_intr", "hard_rule", "output_2","extra_rule"],
}
```

## Design Principles
1. **Modularity** – Each instruction layer is independent for flexible combinations.
2. **Transparency** – All prompt elements are version-controlled for reproducibility.
3. **Comparability** – Multiple taskset versions allow controlled testing of prompt effects.
4. **Cultural Sensitivity** – Language hints help interpret goals in context-specific meaning.
5. **Scalability** – New rule sets, languages, or reasoning schemes can be added without refactoring code.
