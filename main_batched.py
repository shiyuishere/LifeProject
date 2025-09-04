"""
Main script to classify life goals in an Excel file, using batched prompts per ID (row).
Reduces LLM token usage by combining all non-empty goals per person into a single call.
"""

"""
Main script to classify life goals in an Excel file, using batched prompts per ID (row).
Reduces LLM token usage by combining all non-empty goals per person into a single call.
"""

import asyncio
import os
import pandas as pd
import re
from dotenv import load_dotenv
from tqdm import tqdm
from datetime import datetime

from lifeproject import LLMConfigManager
from lifeproject.classifier_batched import classify_text_batch, get_batched_model_response

print("🚀 Starting Batched Life Goal Classification by ID...")

# Load environment variables
load_dotenv()

# Timestamp for saving files
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# File paths
INPUT_PATH = "data/Final_Data - Pilot.xlsx" # change to your input file path
OUTPUT_PATH = f"output/output_classified_batched_by_id_{timestamp}.xlsx"
LOG_PATH = f"output/classification_log_batched_by_id_{timestamp}.csv"
SYSTEM_PROMPT_PATH = "system_prompt.txt"

# Load system prompt
with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
    system_prompt = f.read()

# Load LLM config
provider = os.getenv("LLM_PROVIDER", "openai")
config = LLMConfigManager.get_config(provider)

# Async function to classify each row (person)
async def classify_all_by_id(df: pd.DataFrame, goal_columns: list) -> pd.DataFrame:
    logs = []

    # Ensure output folder
    os.makedirs("output", exist_ok=True)

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="🧠 Classifying by ID"):
        goals_dict = {}
        index_to_col = {}
        counter = 1

        for col in goal_columns:
            val = str(row[col]).strip()
            if val and val.lower() != "nan":
                alias = f"LPSgoal{counter}_content"
                goals_dict[alias] = val
                index_to_col[alias] = col
                counter += 1

        log_entry = {
            "row_index": idx,
            "goal_count": len(goals_dict),
            "gpt_response": "",
            "error": ""
        }

        try:
            if not goals_dict:
                raise ValueError("No goals provided for this row")

            print(f"\n✅ Row {idx} - Goal Aliases: {list(goals_dict.keys())}")

            # Ensure category columns exist for this row's goals
            for alias in goals_dict:
                original_col = index_to_col.get(alias)
                if original_col:
                    cat_col = original_col.replace("_content", "_category")
                    if cat_col not in df.columns:
                        df[cat_col] = ""

            # Call LLM
            response = await get_batched_model_response(config, goals_dict, system_prompt)
            log_entry["gpt_response"] = response[:300]

            print("🤖 LLM Response:\n", response[:500])

            # Parse and write results
            parsed = classify_text_batch(response)
            print("📤 Parsed Result:\n", parsed)

            for alias, categories in parsed.items():
                original_col = index_to_col.get(alias)
                if original_col:
                    category_col = original_col.replace("_content", "_category")
                    df.at[idx, category_col] = ", ".join(categories)
                    print(f"✅ Wrote to {category_col}: {categories}")
                else:
                    print(f"⚠️ Alias {alias} not found in index_to_col")

        except Exception as e:
            log_entry["error"] = str(e)
            print(f"❌ Error in row {idx}:", str(e))
            for col in goal_columns:
                if pd.notna(row[col]) and str(row[col]).strip().lower() != "nan":
                    df.at[idx, col.replace("_content", "_category")] = "Oth"

        logs.append(log_entry)

    # Save log
    log_df = pd.DataFrame(logs)
    os.makedirs("output", exist_ok=True)
    log_df.to_csv(LOG_PATH, index=False)
    print(f"📝 Log saved to {LOG_PATH}")

    return df

# === MAIN ===
if __name__ == "__main__":
    df = pd.read_excel(INPUT_PATH)

    # Detect goal columns
    goal_columns = [col for col in df.columns if re.match(r"LPSgoal\d+_content", col)]

    # Run classification
    df = asyncio.run(classify_all_by_id(df, goal_columns))

    # Reorder columns to put _category after _content
    new_columns = []
    for col in df.columns:
        new_columns.append(col)
        if col.endswith("_content"):
            cat_col = col.replace("_content", "_category")
            if cat_col in df.columns:
                new_columns.append(cat_col)

    # Remove duplicates while preserving order
    seen = set()
    ordered_columns = [x for x in new_columns if not (x in seen or seen.add(x))]
    df = df[ordered_columns]

    # Save result
    df.to_excel(OUTPUT_PATH, index=False)
    print(f"✅ Output saved to: {OUTPUT_PATH}")