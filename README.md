# Life Project: LLM-Based Life-Goal Classification

## Quick Start
```bash
uv sync
uv run python main.py --prompt V4 --model "configs/llms/openai/G41-mini.yaml" --input "input/pt-BR/ptBR_Final_Data_classification.xlsx" --language pt-BR
```

Results will be saved under:

```bash
output/classification/
```

---

##  Project Introduction
This project provides an automated system for classifying life goals using Large Language Models (LLMs). It supports batch processing of Excel datasets, multiple prompt versions (V1–V6), multilingual configurations, and transparent logging of system prompts, user prompts, and classification outputs.

The system is designed for controlled experimentation on how prompt structure affects model behavior and classification outcomes.

---


## Project Structure

```bash
├── main.py                        # Main classification script
├── run_all_combinations.sh        # Run all configuration combinations 
├── evaluation_main.py             # Compare human and LLM classifications
├── kappa.py                       # Cohen’s Kappa for agreement testing
├── Unified_Data.py                # Data merging utility
├── Age_Check.py                   # Age validation
├── translate_EN.py                # English translation of goal texts

├── lifeproject/
│   ├── classifier_batched.py      # Core batched LLM classification logic and build user prompt
│   ├── prompt_builder.py          # Build system prompts
│   ├── llm.py                     # LLM configuration and async client
│   ├── config.py                  # YAML-based model loader

├── configs/
│   ├── llms/
│   │   └── openai/
│   │       ├── G4O-mini.yaml
│   │       ├── G41-mini.yaml
│   │       └── G5.yaml
│   └── prompt/
│       ├── taskset/
│           ├── role.txt
│           ├── ...
│           ├── other prompt component.txt       
│       ├── language_hint/
│       └── codebook/

├── input/                         # Input files for classification and evaluation
│   ├── pt-BR/
│   └── ZH/

├── output/
│   ├── classification/            # Classification results
│   ├── evaluation/                # Evaluation reports
│   ├── kappa/                     # Kappa statistics
│   └── prompt/                    # Saved prompts used in runs

├── requirements.txt
├── pyproject.toml
└── uv.lock
```

---

## Environment Setup
The project uses **uv** for dependency management.

### Install uv
**Windows**:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/MacOS**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install all dependencies
```bash
uv sync
```
OR for quick testing:

```bash
uv pip install -r requirements.in
```

### Set your API key
Create a `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
```

---

## Running the Classification
### Single classification run
```bash
uv run python main.py \
  --prompt V5 --model "configs/llms/openai/G41-mini.yaml" \
  --input "input/pt-BR/ptBR_Final_Data_classification.xlsx" \
  --language "configs/prompt/language_hint/pt-BR.txt" 
```

### Batch execution for all configurations
```bash
chmod +x run_all_combinations.sh
./run_all_combinations.sh
```

---

## Evaluation Tools
### Per-goal accuracy
```bash
uv run python evaluate_accuracy.py
```

### Per-category agreement (Cohen’s Kappa)
```bash
uv run python kappa.py
```

---

## Model & Prompt Configuration

### Model Configuration
Model YAML files are stored under:
```bash
configs/llms/
```
Each file defines:
- API endpoint and key
- Model name
- Temperature
- Token limits
- Pricing and concurrency

Switch models easily by using a different YAML file with the `--model` argument.
More details in `configs/llms/README.md`.

### Prompt Configuration
Prompt files are under:
```bash
configs/prompt/
```

Switch prompt version easily by using a different YAML file with the `--prompt` argument.
More details in `configs/prompt/README.md`

---

## Core Modules and Workflow
### `main.py` — Core entry point
Controls data loading, prompt construction, model calls, and output saving.

**Main workflow:**
1. Parse command-line arguments (paths for input file, taskset, language, and model)
2. Load environment variables (e.g., API key)
3. Load model configuration using `LLMConfigManager.from_yaml()`
4. Build the system prompt with `prompt_builder.load_prompt_components()`
5. Read input Excel data and extract goal texts (goal1–goal15)
6. Call `get_batched_model_response()` for batch classification
7. Save model outputs (classification + reasoning + token usage) as Excel/CSV files

### Evaluation Modules
#### Accuracy Comparison: ` evaluation_main.py ` 
Compares human and LLM classifications goal by goal and generates a mismatch report.
**Workflow:**
1. Load data (human, LLM, and optional English translation)
2. Reshape all datasets to long format with load_and_reshape()
3. Merge by id and loc (same individual and goal)
4. Normalize multi-label categories (e.g., “IR,WEC”)
5. Compute accuracy (exact matches)
6. Generate a mismatch report for all differing cases
7. Save evaluation results under output/evaluation/

#### Inter-Coder Agreement: ` kappa.py `
Calculates **Cohen’s Kappa** per category, mean and weighted Kappa, and significance.
**Workflow:**
1. Read both Excel files (human vs. LLM)
2. Extract all `LPSgoalX_category` columns
3. Identify all unique category labels
4. Build binary matrices for each label (1 = present, 0 = absent)
5. Calculate Kappa, standard error, and p-value
6. Compute mean and weighted mean Kappa
7. Save summarized results to `output/kappa/`

---

### Summary
- **main.py**— pipeline controller
- **config.py + llm.py** — model configuration and API management
- **prompt_builder.py** — system prompt construction
- **classifier_batched.py** — batch classification execution and user prompt construction
- **evaluation_main.py + kappa.py** — evaluation and agreement analysis

---

## Output Files

| Type           | Directory                | 
| -------------- | ------------------------ | 
| Classification | `output/classification/` | 
| Evaluation     | `output/evaluation/`     | 
| Kappa          | `output/kappa/`          | 
| Prompt         | `output/prompt`          |

---

## Notes

- Default codebook: `configs/prompt/codebook/codebook_en.txt`
- Supports multilingual inputs (currently `pt-BR` and `zh-TW`)

---