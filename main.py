"""
Main script to classify life goals in an Excel file (configurable version with argparse).

Usage example:
uv run python main.py --prompt V1 --model "configs/llms/openai/G41-mini.yaml" --input "input/pt-BR/ptBR_Final_Data_classification.xlsx"

uv run python main.py --prompt V2 --model "configs/llms/openai/G41-mini.yaml" --input "input/pt-BR/test.xlsx" --language "configs/prompt/language_hint/pt-BR.txt"
"""

# ==========================================

import argparse
import os
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import asyncio

from lifeproject.config import LLMConfigManager
from lifeproject.prompt_builder import load_prompt
from lifeproject.classifier_batched import get_batched_model_response, classify_text_batch


# ==========================================
# Ensure output folders exist
# ==========================================
def ensure_dirs():
    os.makedirs("output/prompt", exist_ok=True)
    os.makedirs("output/classification", exist_ok=True)


# ==========================================
# Build unique timestamp
# ==========================================
def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ==========================================
# Insert classification results into DataFrame
# ==========================================
def insert_results_into_df(df, row_idx, result_dict, require_reasoning):
    """
    Insert results immediately after each goal content column.
    """
    row = df.iloc[row_idx]

    for goal_key, content in row.items():
        if not goal_key.lower().startswith("lpsgoal"):
            continue

        if not goal_key.endswith("_content"):
            continue

        content_value = str(content).strip()
        if content_value.lower() in ("", "nan"):
            continue  # Skip empty goals entirely

        base = goal_key[:-8]  # remove "_content"
        cat_col = f"{base}_category"
        rea_col = f"{base}_reasoning"

        # Insert position: right after the content column
        insert_loc = df.columns.get_loc(goal_key) + 1

        # Create category column if missing
        if cat_col not in df.columns:
            df.insert(insert_loc, cat_col, "")

        categories = result_dict.get(base, {}).get("categories", [])
        df.at[row_idx, cat_col] = ", ".join(categories)

        # Only V3–V6: include reasoning column
        if require_reasoning:
            if rea_col not in df.columns:
                df.insert(insert_loc + 1, rea_col, "")
            reasoning = result_dict.get(base, {}).get("reasoning", "")
            df.at[row_idx, rea_col] = reasoning


# ==========================================
# Main Classification Pipeline
# ==========================================
async def run_classification(args):
    print("🚀 Starting Batched Life Goal Classification...")
    ensure_dirs()

    # Load input
    input_path = args.input
    df = pd.read_excel(input_path)
    print(f"📥 Loaded dataset: {input_path} ({len(df)} rows)")

    # Load model config
    print(f"⚙️ Loading model config from: {args.model}")
    config = LLMConfigManager.from_yaml(args.model)

    # ✅ Client IS config (no OpenAIClient wrapper needed)
    client = config

    # Load prompt
    print(f"🧩 Building system prompt for version: {args.prompt}")
    language = args.language if args.language else "none"
    system_prompt, require_reasoning = load_prompt(args.prompt, language, args.codebook)


    # Save system prompt
    sys_filename = f"systemprompt_{args.prompt}_{language}_{config.model}_{timestamp()}.txt"
    sys_filepath = os.path.join("output/prompt", sys_filename)
    with open(sys_filepath, "w", encoding="utf-8") as f:
        f.write(system_prompt)
    print(f"✅ System prompt saved to: {sys_filepath}")

    # Prepare user prompt log
    user_prompts_log = []

    results_df = df.copy()
    token_counts = {"in": 0, "out": 0}

    print("🔍 Classifying rows...\n")

    for idx in tqdm(range(len(df)), desc="Classifying"):
        row = df.iloc[idx]

        # Collect non-empty goals
        goals_dict = {}
        for col in df.columns:
            if col.lower().startswith("lpsgoal") and col.endswith("_content"):
                value = str(row[col]).strip()
                if value.lower() not in ("", "nan"):
                    base = col[:-8]
                    goals_dict[base] = value

        if not goals_dict:
            continue

        # Build user prompt (same logic as classifier)
        goals_text = "\n".join([f"{k}: {v}" for k, v in goals_dict.items()])
        if require_reasoning:
            request = (
                "Return the results as a JSON object, where each goal identifier maps to "
                "`categories` and a short `reasoning`."
            )
        else:
            request = (
                "Return the results as a JSON object, where each goal identifier maps to "
                "`categories` only."
            )
        user_prompt = (
            "The following are the life goals expressed by a person:\n\n"
            f"{goals_text}\n\n"
            f"{request}"
        )

        user_prompts_log.append(f"=== Respondent {idx+1} ===\n{user_prompt}\n\n")

        # Call model
        resp = await get_batched_model_response(
            client,
            goals_dict,
            system_prompt,
            require_reasoning,
            token_counts
        )

        # Parse
        try:
            parsed = classify_text_batch(resp)
        except Exception:
            parsed = {}

        # Insert results
        insert_results_into_df(results_df, idx, parsed, require_reasoning)

    # Save user prompts
    up_filename = f"userprompt_{args.prompt}_{language}_{config.model}_{timestamp()}.txt"
    up_filepath = os.path.join("output/prompt", up_filename)
    with open(up_filepath, "w", encoding="utf-8") as f:
        f.write("".join(user_prompts_log))
    print(f"✅ User prompts saved to: {up_filepath}")

    # ✅ Save classification result (new correct naming)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_filename = f"{base_name}_classification_{config.model}_{args.prompt}_{timestamp()}.xlsx"
    output_path = os.path.join("output/classification", out_filename)
    results_df.to_excel(output_path, index=False)

    print(f"✅ Classification saved to: {output_path}")
    print("\n🎯 All done!")
    print(f"🔢 Total prompt tokens: {token_counts['in']}")
    print(f"🔢 Total completion tokens: {token_counts['out']}")


# ==========================================
# CLI Entry
# ==========================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True, help="Prompt version V1-V6")
    parser.add_argument("--model", required=True, help="Model config YAML")
    parser.add_argument("--input", required=True, help="Input Excel file")
    parser.add_argument("--language", help="Language code, required only for V3-V6")
    parser.add_argument("--codebook", help="Path to custom codebook file")
    args = parser.parse_args()

    asyncio.run(run_classification(args))


if __name__ == "__main__":
    main()
