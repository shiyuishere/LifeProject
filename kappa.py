# Kappa measures consistency between two coders.
# By category (one of 13 labels) → Check each cell in 15 columns to see if it contains the label
# In multiple encodings (such as "WEC, FS"), this is 1 for WEC and also 1 for FS
# ==========================================
import pandas as pd
import numpy as np
from scipy.stats import norm
import os
from datetime import datetime

# Set the file paths
file1 = "input/pt-BR/ptBR_Final_Data_evaluation.xlsx"      # Human annotation
file2 = "output/classification/ptBR_Final_Data_classification_classification_gpt-4.1-mini_V3_20251124_144759.xlsx"  # LLM classification

# Timestamp for saving files
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

OUTPUT_DIR = "output/Kappa"
os.makedirs(OUTPUT_DIR, exist_ok=True)
base_name = os.path.splitext(os.path.basename(file2))[0]
OUTPUT_PATH = os.path.join(OUTPUT_DIR, f"{base_name}_{timestamp}.xlsx")

# Read the Excel files
df1 = pd.read_excel(file1)
df2 = pd.read_excel(file2)

# All category fields (goal1 to goal15)
category_cols = [f"LPSgoal{i}_category" for i in range(1, 16)]

# Extract all individual labels (without combinations)
all_labels = pd.concat([df1[category_cols], df2[category_cols]], axis=0).values.ravel()
all_labels = pd.Series(all_labels).dropna().astype(str)

# Split combined labels into multiple individual labels
split_labels = all_labels.str.split(",\s*")  # Split by comma and optional space
flat_labels = [label.strip() for sublist in split_labels for label in sublist]

# Remove empty string labels
flat_labels = [label for label in flat_labels if label.strip() != ""]

# Remove duplicates and sort
all_labels = sorted(set(flat_labels))

# Function to interpret kappa values
def interpret_kappa(kappa):
    if pd.isna(kappa):
        return "N/A"
    elif kappa < 0:
        return "Less than chance"
    elif kappa < 0.21:
        return "Poor"
    elif kappa < 0.41:
        return "Fair"
    elif kappa < 0.61:
        return "Moderate"
    elif kappa < 0.81:
        return "Substantial"
    elif kappa < 1:
        return "Almost perfect"
    else:
        return "Perfect"

# Calculate the consistency for each category
results = []

for label in all_labels:
    coder1_binary = []
    coder2_binary = []

    for col in category_cols: # str.contains(rf"\b{label}\b") → ✅ 1; ❌ 0
        coder1_binary.extend((df1[col].fillna("").str.contains(rf"\b{label}\b")).astype(int).tolist())
        coder2_binary.extend((df2[col].fillna("").str.contains(rf"\b{label}\b")).astype(int).tolist())

    # Count occurrences
    human_count = sum(coder1_binary)
    llm_count = sum(coder2_binary)
    total_count = human_count + llm_count

    # Confusion matrix
    table = pd.crosstab(pd.Series(coder1_binary, name='coder1'),
                        pd.Series(coder2_binary, name='coder2')).reindex(index=[0,1], columns=[0,1], fill_value=0)

    a = table.loc[1, 1]
    b = table.loc[1, 0]
    c = table.loc[0, 1]
    d = table.loc[0, 0]
    N = a + b + c + d

    Po = (a + d) / N
    p1 = (a + b) / N
    p2 = (a + c) / N
    Pe = p1 * p2 + (1 - p1) * (1 - p2)

    kappa = (Po - Pe) / (1 - Pe) if (1 - Pe) != 0 else np.nan
    se = np.sqrt(Po * (1 - Po) / (N * (1 - Pe) ** 2)) if (1 - Pe) != 0 else np.nan
    z = kappa / se if se > 0 else np.nan
    p_value = 2 * (1 - norm.cdf(abs(z))) if not np.isnan(z) else np.nan

    results.append({
        "Category": label,
        "Human_Count": human_count,
        "LLM_Count": llm_count,
        "Total_Count": total_count,
        "Kappa": kappa,
        "p-value": p_value,
        "Significance": "*" if p_value < 0.05 else "",
        "Agreement Level": interpret_kappa(kappa)
    })

# Convert to DataFrame
results_df = pd.DataFrame(results)
results_df["Kappa"] = results_df["Kappa"].round(3)
results_df["p-value"] = results_df["p-value"].round(5)

# ---- NEW: Compute mean and weighted mean Kappa ----
mean_kappa = results_df["Kappa"].mean()

results_df["Weight"] = results_df["Total_Count"] / results_df["Total_Count"].sum()

# Keep a numeric weight column for internal computation
weighted_mean_kappa = (results_df["Kappa"] * results_df["Weight"]).sum()

# Convert weight to percentage display format with two decimals
results_df["Weight"] = (results_df["Weight"] * 100).round(2).astype(str) + "%"


# Append summary rows
results_df.loc[len(results_df)] = ["Mean Kappa", "", "", "", mean_kappa, "", "", interpret_kappa(mean_kappa), ""]
results_df.loc[len(results_df)] = ["Weighted Mean Kappa", "", "", "", weighted_mean_kappa, "", "", interpret_kappa(weighted_mean_kappa), ""]

# Save to Excel
results_df.to_excel(OUTPUT_PATH, index=False)

print("✅ Finished processing. Results saved to:", OUTPUT_PATH)
print("📌 Mean Kappa:", round(mean_kappa, 3))
print("📌 Weighted Mean Kappa:", round(weighted_mean_kappa, 3))
