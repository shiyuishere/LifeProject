# Life Goal Classification using LLMs

This project classifies life goals into structured categories using large language models (LLMs) via API calls. It reads life goal data from Excel files, classifies them using a prompt aligned with a predefined codebook, and optionally evaluates the classification accuracy against manual labels.



## 🔄 Update: Batched Classification (batch-llm-call branch)
This branch introduces a more efficient version of the classification logic with key updates:
- Use main_batched.py instead of main.py
- Combine all non-empty goals per person (row) into a single LLM call, reducing token usage
- Replace categories.json with system_prompt.txt, which ensures full alignment with the current codebook
- Same output structure as before: one classification per goal column
- Update evaluate_accuracy.py to output classification accuracy by category and by person, and to list all cases with classification differences

To run the new version:

```bash
uv run python main_batched.py
```



## 🗂️ Project Structure(Updated)

```
FTOLP_LLM/
├── README.md
├── data                                                # Input data folder
│   └── Final_Data_Pilot_test.xlsx                      # Excel file with life goals to classify
├── evaluate                                            # Manual labels and evaluation folder
│   ├── Final_Data_Pilot_test_ea.xlsx                   # Manually coded life goal categories
│   └── output/                                         # Output of evaluation results folder
├── evaluate_accuracy.py                                # Script to compare LLM output with manual labels
├── lifeproject                                         # Core Python package (classification logic & config)
│   ├── __init__.py                                     # Package initialization
│   ├── __pycache__/                                    # (Generated) Cache directory folder
│   ├── classifier_batched.py                           # Main classification logic using LLM for main_batched.py
│   ├── prompt_builder.py                               # System prompt for main_batched.py
│   ├── config.py                                       # LLM config management (loads .env)
│   └── llm.py                                          # LLM config dataclass and OpenAI interface
├── main_batched.py                                     # Main script to classify life goals in an Excel file using batched LLM requests
├── output/                                             # Output data folder
├── pyproject.toml                                      # Project metadata and configuration
├── requirements.in                                     # Editable dependency list
├── system_prompt.txt                                   # System prompt template for guiding LLM
├── uv.lock                                             # (Generated) Locked dependency versions
├── .env                                                # Environment variables (API key, model name)
└── .gitignore                                          # Telling Git which files or directories to ignore and exclude from version control
```



## 🛠️ How to Run the Project

### 1. Set up the environment

Create a virtual environment and install dependencies:

```bash
uv venv
uv pip compile requirements.in --output uv.lock
uv pip sync uv.lock
```

Alternatively:
```bash
uv sync
```

> Make sure you have [`uv`](https://github.com/astral-sh/uv) installed beforehand, installation process is as follows:
    
Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Linux/MacOS:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```


### 2. Add your API keys
Create a `.env` file in the project root directory based on this template:
```env
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o
LLM_PROVIDER=openai
```



### 3. Run the classification

```bash
uv run python main_batched.py
```

This will:

- Load input Excel file (`data/input_test.xlsx`)
- Classify goals using LLM based on `categories.json`
- Save results to `output/output_classified_<timestamp>.xlsx`
- Log outputs and errors to `output/`



### 4. Evaluate classification accuracy (optional)

```bash
uv run python evaluate_accuracy.py
```

This script compares the LLM output with manually labeled data (`evaluate/input_ea.xlsx`), generates a bar plot of accuracies, and outputs mismatch details.


## 📝 Note

- The old script main.py is deprecated and will be removed in future versions.
- classifier.py has been replaced by classifier_batched.py and prompt_builder.py.
- The input file has been updated to Final_Data_Pilot_test.xlsx, and the evaluation input file has been updated to Final_Data_Pilot_test_ea.xlsx.
- A new repository named LifeProject has been initialized on GitHub to manage core classification modules.


## Contact
FTOLP is a project by the [ODISSEI Social Data Science (SoDa) team](https://odissei-data.nl/nl/event/soda-data-drop-in/). Do you have questions, suggestions, or remarks on the technical implementation? Create an issue in the issue tracker or feel free to contact [Qixiang Fang](https://github.com/fqixiang) or [Shiyu Dong](https://github.com/shiyuishere).

<img width="1387" height="469" alt="soda" src="https://github.com/user-attachments/assets/b71ef1fa-0bda-449c-bd03-af356f616087" />
