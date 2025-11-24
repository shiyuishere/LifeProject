import pandas as pd
import numpy as np
import os
import re
from datetime import datetime

# ===============================
# 1) Configuration 
# ===============================
# human-annotated data, containing content in the original language
HUMAN_PATH = "input/pt-BR/ptBR_Final_Data_evaluation.xlsx" # ← Change this

# LLM classification result path
LLM_PATH = "output/classification/ptBR_Final_Data_classification_classification_gpt-4.1-mini_V3_20251124_144759.xlsx" # ← Change this

# English translation version path
EN_HUMAN_PATH = "input/pt-BR/ptBR_Final_Data_evaluation_EN.xlsx"  # ← Change this

# Automatic detection of language code, extracting from path
LANG_CODE = os.path.basename(os.path.dirname(HUMAN_PATH))

# Create output directory
OUTPUT_DIR = "output/evaluation"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Generate timestamp
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Extract file base name from LLM_PATH (without extension)
base_llm_name = os.path.splitext(os.path.basename(LLM_PATH))[0]

# Output filename format:
# e.g.,  ZH Data_classification_20251023_223746_evaluated_20250103_231812.xlsx
OUTPUT_PATH = os.path.join(OUTPUT_DIR, f"{base_llm_name}_evaluated_{TIMESTAMP}.xlsx")

# ===============================
# 2) Data Loading and Standardization
# ===============================
def load_and_reshape(file_path, data_type, lang_code=None):
    """
    Load the data, standardize the column names, and reshape it into a long format.
    
    Args:
        file_path: Excel file path
        data_type: 'manual' (human annotations), 'llm' (LLM classification), 'en' (EN translation)
        lang_code: language code for dynamically named columns
    
    Returns:
        reshaped DataFrame
    """

    df = pd.read_excel(file_path)

    # Ensure there's an 'id' column for merging
    if 'id' not in df.columns:
        df.insert(0, 'id', df.index + 1)
    
    # Dynamically identify related columns
    goal_cols = [col for col in df.columns if re.match(r"LPSgoal\d+_", col)]
    
    # Reshape a wide table into a long table
    df_long = pd.melt(
        df, 
        id_vars=['id'], 
        value_vars=goal_cols, 
        var_name='goal_col', 
        value_name='value'
    )

    # Drop rows with NaN values in 'value' column
    df_long = df_long.dropna(subset=['value'])
    
    # Extract the location number of the goal (locl: location)
    df_long['locl'] = df_long['goal_col'].str.extract(r"LPSgoal(\d+)")

    # Extract the type of the column (content, category, reasoning, etc.)
    df_long['col_type'] = df_long['goal_col'].str.extract(r"_(content|category|reasoning|manual|age)")
    
    # Pivot table: use column type as column name so that each goal occupies one row
    df_pivoted = df_long.pivot_table(
        index=['id', 'locl'],
        columns='col_type',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    # Rename columns based on data type to prevent merge conflicts
    if data_type == 'manual':
        # Human-annotated data: retaining content and classification in the original language
        # Assuming manual annotation is in a column named 'category' or 'manual'
        cat_col = 'category' if 'category' in df_pivoted.columns else 'manual' 

        rename_dict = {
            cat_col: 'LPSgoal_category_manual',  # human annotations
            'content': f'LPSgoal_content_{lang_code}',  # original content
        }

        # Include age if present
        if 'age' in df_pivoted.columns:
            rename_dict['age'] = 'LPSgoal_age'
    
        df_pivoted.rename(columns=rename_dict, inplace=True)

    elif data_type == 'llm':
        # LLM classification results including category, reasoning
        rename_dict = {
            'category': f'LPSgoal_category_{lang_code}',  # LLM classification
            'reasoning': f'LPSgoal_reasoning_{lang_code}',  # LLM reasoning
        }

        # If there is a content column in the LLM output (there may be in some cases)
        if 'content' in df_pivoted.columns:
            rename_dict['content'] = f'LPSgoal_content_{lang_code}_llm'
            
        df_pivoted.rename(columns=rename_dict, inplace=True)
        
    elif data_type == 'en':
        # English translation version for understanding
        rename_dict = {
            'content': 'LPSgoal_content_EN',  # English content
        }
        
        # If the English version also has category and reasoning (usually not needed, but just in case)
        if 'category' in df_pivoted.columns:
            rename_dict['category'] = 'LPSgoal_category_EN'
        if 'reasoning' in df_pivoted.columns:
            rename_dict['reasoning'] = 'LPSgoal_reasoning_EN'
            
        df_pivoted.rename(columns=rename_dict, inplace=True)

    # Make sure necessary columns exist (even if empty)
    if data_type == 'manual' and 'LPSgoal_category_manual' not in df_pivoted.columns:
        df_pivoted['LPSgoal_category_manual'] = np.nan
        
    return df_pivoted

def normalize_categories(categories):
    """
    Normalize multi-label classification for easier comparison
     
    Processing method:
    1. stripping spaces
    2. sorting alphabetically ("IR,WEC" == "WEC,IR")
    
    Args:
        categories: Category string, such as "IR,WEC" or "FS"

    Returns:
        normalized category string
    """
    if pd.isna(categories) or str(categories).strip() == '':
        return ''
    
    # Split, remove spaces, sort, regroup
    return ','.join(sorted([c.strip() for c in str(categories).split(',')]))

# ===============================
# 3) Main Execution
# ===============================
print(f"Detecting language code: {LANG_CODE}")
print("Loading, normalizing and reshaping data...")

# Load data
df_manual = load_and_reshape(HUMAN_PATH, 'manual', LANG_CODE)
df_llm = load_and_reshape(LLM_PATH, 'llm', LANG_CODE)

# Try loading the English translation version if it exists
df_en = None
if os.path.exists(EN_HUMAN_PATH):
    print(f"English translation file found: {EN_HUMAN_PATH}")
    df_en = load_and_reshape(EN_HUMAN_PATH, 'en', LANG_CODE)
else:
    print(f"English translation file not found: {EN_HUMAN_PATH}, will continue processing without the English translation column")

# ===============================
# 4) Merge Data
# ===============================
print("Merging data...")

# Use id and locl as keys, gradually merge all data
final_df = pd.merge(
    df_manual, 
    df_llm, 
    on=['id', 'locl'], 
    how='outer', 
    suffixes=('', '_llm_dup')
)

# If there is an English translation, it will also be incorporated.
if df_en is not None:
    final_df = pd.merge(
        final_df, 
        df_en, 
        on=['id', 'locl'], 
        how='outer',
        suffixes=('', '_en_dup')
    )

# ===============================
# 5) Data Preparation for Evaluation
# ===============================
print("Preparing evaluation data...")

# Create normalized categorical columns
final_df['norm_manual'] = final_df['LPSgoal_category_manual'].apply(normalize_categories)

# Dynamically obtain LLM classification column names
llm_category_col = f'LPSgoal_category_{LANG_CODE}'
if llm_category_col in final_df.columns:
    final_df['norm_llm'] = final_df[llm_category_col].apply(normalize_categories)
else:
    print(f"Warning: LLM classification column not found '{llm_category_col}'")
    final_df['norm_llm'] = ''

# Filter out rows where both manual and LLM results are empty (no goal was present)
evaluation_df = final_df[
    (final_df['norm_manual'] != '') | (final_df['norm_llm'] != '')
].copy()

# ===============================
# 6) Evaluation Metrics Calculation
# ===============================
print("\n" + "="*60)
print("Calculate performance metrics")
print("="*60)

# Align the two columns for comparison
y_true = evaluation_df['norm_manual']
y_pred = evaluation_df['norm_llm']

# Calculate simple match count
total_records_compared = len(evaluation_df)
matches = (y_true == y_pred).sum()
mismatch_count = total_records_compared - matches
accuracy = matches / total_records_compared if total_records_compared > 0 else 0

print(f"Total number of records evaluated: {total_records_compared}")
print(f"Number of exact matches: {matches}")
print(f"Mismatch count: {mismatch_count}")
print(f"Exact match accuracy (LLM vs. human): {accuracy:.2%} ({matches}/{total_records_compared})")

# ===============================
# 7) Filter and Prepare Mismatch Report
# ===============================
print("\n" + "="*60)
print("Generating Mismatch Report")
print("="*60)

# Filter inconsistent rows (where normalized categories do not match)
mismatch_df = evaluation_df[y_true != y_pred].copy()

# Dynamically build output column list in the desired order
output_columns = ['id', 'locl']

# Add original language content column
original_content_col = f'LPSgoal_content_{LANG_CODE}'
if original_content_col in mismatch_df.columns:
    output_columns.append(original_content_col)

# Add English translation column if present
if 'LPSgoal_content_EN' in mismatch_df.columns:
    output_columns.append('LPSgoal_content_EN')

# Add age column if present
if 'LPSgoal_age' in mismatch_df.columns:
    output_columns.append('LPSgoal_age')

# Add manual category column
if 'LPSgoal_category_manual' in mismatch_df.columns:
    output_columns.append('LPSgoal_category_manual')

# Add LLM category column
if llm_category_col in mismatch_df.columns:
    output_columns.append(llm_category_col)

# Add LLM reasoning column
llm_reasoning_col = f'LPSgoal_reasoning_{LANG_CODE}'
if llm_reasoning_col in mismatch_df.columns:
    output_columns.append(llm_reasoning_col)

# Only select columns that exist in the mismatch_df
output_columns = [col for col in output_columns if col in mismatch_df.columns]

# Create the final mismatch data frame
final_mismatch_df = mismatch_df[output_columns].copy()

# Rename columns to make them more readable
rename_map = {
    original_content_col: f'LPSgoal_content_{LANG_CODE}_Original',
    llm_category_col: f'LPSgoal_category_{LANG_CODE}_LLM',
    llm_reasoning_col: f'LPSgoal_reasoning_{LANG_CODE}_LLM'
}

# Rename only existing columns
rename_map = {k: v for k, v in rename_map.items() if k in final_mismatch_df.columns}
final_mismatch_df.rename(columns=rename_map, inplace=True)

# ===============================
# 8) Save the Final Result 
# ===============================
print("\nSaving evaluation results to:", OUTPUT_PATH)

if final_mismatch_df.empty:
    print("No records with inconsistent classification were found. No file is generated.")
    print("\n🎉 Congratulations! All categories are the same!")
else:
    print(f"{len(final_mismatch_df)} inconsistent records found")
    
    # Save to Excel without styling
    final_mismatch_df.to_excel(OUTPUT_PATH, engine='openpyxl', index=False)
    print("✅ Finished!")
    print(f"\nThe evaluation report has been saved to: {OUTPUT_PATH}")
    print(f"\nColumns included in the report:")
    for col in final_mismatch_df.columns:
        print(f"  - {col}")
    
print("\n" + "="*60)
print("Evaluation process ended")
print("="*60)