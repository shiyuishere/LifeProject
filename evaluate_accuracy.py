import pandas as pd
import re
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from tqdm import tqdm

# === 1. Timestamp and Path Config ===
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_DIR = os.path.join(BASE_DIR, "evaluate")
INPUT_MANUAL = os.path.join(EVAL_DIR, "Final_Data - Pilot_ea.xlsx")
OUTPUT_DIR = os.path.join(EVAL_DIR, "output")

# Output files with timestamp
PLOT_PATH = os.path.join(OUTPUT_DIR, f"accuracy_by_goal_{TIMESTAMP}.png")
LOG_PATH = os.path.join(OUTPUT_DIR, f"evaluate_accuracy_{TIMESTAMP}.log")

# Input LLM output from main.py
LLM_SOURCE_DIR = os.path.join(BASE_DIR, "output")

# === 2. Find Latest Output File ===
def find_latest_output_file(directory=LLM_SOURCE_DIR, prefix="output_classified_", ext=".xlsx"):
    print(f"🔍 Scanning directory: {directory}")
    try:
        all_files = os.listdir(directory)
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ Directory not found: {directory}")
    matched = [
        os.path.join(directory, f)
        for f in all_files
        if f.startswith(prefix) and f.endswith(ext)
    ]
    print(f"🧾 Matched files: {matched}")
    if not matched:
        raise FileNotFoundError("❌ No classified output files found.")
    return max(matched, key=os.path.getmtime)

# === 3. Helper Functions ===
def get_goal_column_pairs(df_llm, df_manual):
    auto_cols = [col for col in df_llm.columns if re.match(r"LPSgoal\d+_category", col)]
    pairs = []
    for auto_col in auto_cols:
        goal_num = re.search(r"LPSgoal(\d+)_category", auto_col).group(1)
        manual_col = f"LPSgoal{goal_num}_manual"
        if manual_col in df_manual.columns:
            pairs.append((auto_col, manual_col))
    return pairs

def parse_codes(code_str):
    if pd.isna(code_str):
        return set()
    return set([c.strip().upper() for c in str(code_str).split(",") if c.strip()])

def compare_exact_match(auto_set, manual_set):
    return auto_set == manual_set

# === 4. Evaluation ===
def evaluate_accuracy(df_llm, df_manual, column_pairs):
    results = []
    total_correct = 0
    total_total = 0
    per_goal_records = []

    for auto_col, manual_col in column_pairs:
        correct = 0
        total = 0
        goal_name = auto_col.replace("_category", "")

        for idx in tqdm(df_llm.index, desc=f"⏳ Evaluating {auto_col}"):
            row_id = df_llm.at[idx, "id"] if "id" in df_llm.columns else idx
            auto_codes = parse_codes(df_llm.at[idx, auto_col])
            manual_codes = parse_codes(df_manual.at[idx, manual_col])

            if not manual_codes:
                continue

            total += 1
            match = compare_exact_match(auto_codes, manual_codes)
            if match:
                correct += 1

            per_goal_records.append({
                "id": row_id,
                "Goal": goal_name,
                "LLM Output": ", ".join(auto_codes),
                "Manual Label": ", ".join(manual_codes),
                "Goal Text": df_llm.at[idx, auto_col.replace("_category", "_content")],
            })

        acc = correct / total if total > 0 else None
        results.append({
            "Goal": goal_name,
            "Correct": correct,
            "Total": total,
            "Accuracy (%)": round(acc * 100, 2) if acc is not None else "N/A"
        })

        total_correct += correct
        total_total += total

    overall_acc = round(total_correct / total_total * 100, 2) if total_total > 0 else 0.0
    return results, overall_acc, per_goal_records

# === 5. Main Program ===
if __name__ == "__main__":
    print("📊 Evaluating LLM classification accuracy...")

    # Ensure output folder exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        LLM_OUTPUT_PATH = find_latest_output_file()
        print(f"🗂 Using latest LLM output file: {LLM_OUTPUT_PATH}")
        df_llm = pd.read_excel(LLM_OUTPUT_PATH)
        df_manual = pd.read_excel(INPUT_MANUAL)
    except Exception as e:
        print(f"❌ Error loading files: {e}")
        exit(1)

    pairs = get_goal_column_pairs(df_llm, df_manual)
    if not pairs:
        print("❌ No matching goal columns found between LLM and manual data.")
        exit()

    results, overall_acc, per_goal_records = evaluate_accuracy(df_llm, df_manual, pairs)

    # === Build comparison DataFrame ===
    correct_per_goal = pd.DataFrame(per_goal_records)
    correct_per_goal["LLM Output Set"] = correct_per_goal["LLM Output"].apply(lambda x: set(s.strip() for s in x.split(",")))
    correct_per_goal["Manual Label Set"] = correct_per_goal["Manual Label"].apply(lambda x: set(s.strip() for s in x.split(",")))
    correct_per_goal["Match"] = correct_per_goal["LLM Output Set"] == correct_per_goal["Manual Label Set"]

    # === Save only mismatches ===
    per_goal_df_mismatch = correct_per_goal[correct_per_goal["Match"] == False]
    PERGOAL_PATH = os.path.join(OUTPUT_DIR, f"per_goal_comparison_{TIMESTAMP}.xlsx")
    per_goal_df_mismatch.drop(columns=["LLM Output Set", "Manual Label Set", "Match"]).to_excel(PERGOAL_PATH, index=False)
    print(f"\n📄 Per-goal mismatches saved to: {PERGOAL_PATH}")

    # === Per-person accuracy ===
    person_accuracy = correct_per_goal.groupby("id")["Match"].agg(["sum", "count"]).reset_index()
    person_accuracy["Accuracy"] = (person_accuracy["sum"] / person_accuracy["count"]).round(2)

    # === Per-category accuracy ===
    rows = []
    for _, row in correct_per_goal.iterrows():
        for cat in row["Manual Label Set"]:
            rows.append({
                "id": row["id"],
                "Goal": row["Goal"],
                "Category": cat,
                "Correct": cat in row["LLM Output Set"]
            })
    category_df = pd.DataFrame(rows)
    category_accuracy = category_df.groupby("Category")["Correct"].agg(["sum", "count"]).reset_index()
    category_accuracy["Accuracy"] = (category_accuracy["sum"] / category_accuracy["count"]).round(2)

    # === Save accuracy breakdown ===
    ACCURACY_BREAKDOWN_PATH = os.path.join(OUTPUT_DIR, f"accuracy_breakdown_{TIMESTAMP}.xlsx")
    with pd.ExcelWriter(ACCURACY_BREAKDOWN_PATH) as writer:
        person_accuracy.to_excel(writer, sheet_name="Per_Person_Accuracy", index=False)
        category_accuracy.to_excel(writer, sheet_name="Per_Category_Accuracy", index=False)
    print(f"\n📊 Extra accuracy breakdown saved to: {ACCURACY_BREAKDOWN_PATH}")

    # === Print summary ===
    print("\n✅ Accuracy Report:")
    for r in results:
        print(f"{r['Goal']}: {r['Accuracy (%)']}% ({r['Correct']}/{r['Total']})")
    print(f"\n🎯 Overall Accuracy: {overall_acc}%")

    # === Plot per-category accuracy ===
    plt.figure(figsize=(10, 6))
    sns.barplot(x="Accuracy", y="Category", data=category_accuracy, palette="Blues_d")
    plt.title("LLM Classification Accuracy by Category", fontsize=14)
    plt.xlabel("Accuracy")
    plt.ylabel("Category")
    plt.xlim(0, 1)
    plt.tight_layout()
    plt.savefig(PLOT_PATH)
    print(f"\n📊 Accuracy plot saved to: {PLOT_PATH}")

    # === Log output ===
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n🕓 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"✅ Used LLM Output File: {LLM_OUTPUT_PATH}\n")
        f.write(f"📋 Manual Labels File: {INPUT_MANUAL}\n")
        f.write(f"🎯 Overall Accuracy: {overall_acc}%\n")
        for r in results:
            f.write(f"  - {r['Goal']}: {r['Accuracy (%)']}% ({r['Correct']}/{r['Total']})\n")
    print(f"\n📝 Log saved to: {LOG_PATH}")

    print("✅ Evaluation completed successfully!")