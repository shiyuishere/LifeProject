import pandas as pd

# =============================
# 1. File configuration
# =============================
files = {
    "V0_original": "output/evaluation/ptBR_Final_Data _classification_20251106_114334_evaluated_20251106_121110.xlsx",
    "V1": "output/evaluation/ptBR_Final_Data_classification_G41-mini_V1_20251117_162409_evaluated_20251117_230321.xlsx",
    "V2": "output/evaluation/ptBR_Final_Data_classification_G41-mini_V2_20251117_171826_evaluated_20251117_230607.xlsx",
    "V3": "output/evaluation/ptBR_Final_Data_classification_G41-mini_V3_20251117_180515_evaluated_20251117_230844.xlsx",
    "V4": "output/evaluation/ptBR_Final_Data_classification_G41-mini_V4_20251117_155349_evaluated_20251117_231040.xlsx",
    "V5": "output/evaluation/ptBR_Final_Data_classification_G41-mini_V5_20251117_182916_evaluated_20251117_231141.xlsx",
}

# Dictionary for presence tracking
presence = {}

# =============================
# 2. Read files and extract (id, locl)
# =============================
for name, path in files.items():
    df = pd.read_excel(path)

    # Check required columns
    if not {"id", "locl"}.issubset(df.columns):
        raise ValueError(f"File {path} is missing required columns: 'id', 'locl'")

    # Construct unique key
    df["key"] = df["id"].astype(str) + "_" + df["locl"].astype(str)

    # Update presence dictionary
    for key in df["key"]:
        if key not in presence:
            presence[key] = {f: 0 for f in files.keys()}
        presence[key][name] = 1

# =============================
# 3. Convert presence info into a DataFrame
# =============================
matrix_df = pd.DataFrame([
    {"id": k.split("_")[0], "locl": k.split("_")[1], **presence[k]}
    for k in presence
])

matrix_df = matrix_df.sort_values(by=["id", "locl"])

# =============================
# 4. Change tracking
# =============================
change_report = []
stable_records = []

file_order = list(files.keys())

for idx, row in matrix_df.iterrows():
    key = f"{row['id']}_{row['locl']}"
    presence_vector = [row[f] for f in file_order]

    # Detect stable patterns (no change across versions)
    if all(x == presence_vector[0] for x in presence_vector):
        stable_records.append(key)
        continue

    # Track appearance/disappearance
    transitions = []
    for i in range(len(file_order) - 1):
        curr_file = file_order[i]
        next_file = file_order[i + 1]

        if presence_vector[i] == 0 and presence_vector[i + 1] == 1:
            transitions.append(f"Appeared in {next_file} (was missing in {curr_file})")

        elif presence_vector[i] == 1 and presence_vector[i + 1] == 0:
            transitions.append(f"Disappeared in {next_file} (was present in {curr_file})")

    change_report.append({
        "id": row["id"],
        "locl": row["locl"],
        "presence_pattern": presence_vector,
        "changes": "; ".join(transitions) if transitions else "Changed but no clear transitions"
    })

change_df = pd.DataFrame(change_report)
stable_df = pd.DataFrame(stable_records, columns=["id_locl"])

# =============================
# 5. Save results
# =============================
output_matrix = "output/evaluation/id_locl_presence_matrix.xlsx"
output_changes = "output/evaluation/id_locl_change_report.xlsx"
output_stable = "output/evaluation/id_locl_stable_records.xlsx"

matrix_df.to_excel(output_matrix, index=False)
change_df.to_excel(output_changes, index=False)
stable_df.to_excel(output_stable, index=False)

print("\n=== Analysis Complete ===")
print("Presence matrix saved to:", output_matrix)
print("Change report saved to:", output_changes)
print("Stable records saved to:", output_stable)

print("\nNotes:")
print("- 'presence_matrix' shows which (id, locl) appears in each version")
print("- 'change_report' lists only records that changed")
print("- 'stable_records' lists records unchanged across all 6 versions")
