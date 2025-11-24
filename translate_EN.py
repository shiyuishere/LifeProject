import os
import pandas as pd
from openai import OpenAI # call LLM
from dotenv import load_dotenv
from tqdm import tqdm

# ==============================
# 1) LOAD ENV + API CLIENT
# ==============================
# seting environment variables in .env file
load_dotenv()  # read .env automatically

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print("✅ Key loaded:", bool(os.getenv("OPENAI_API_KEY")))
print("🔑 Key preview:", os.getenv("OPENAI_API_KEY")[:10])

# ==============================
# 2) EDIT LANGUAGE AND FILES PATHS HERE
# ==============================
SOURCE_LANGUAGE = "Brazilian Português"   # ← Change this
INPUT_FILE  = "data/pt-BR/ptBR_Final_Data _evaluation.xlsx"  # ← Change this
OUTPUT_FILE = "data/pt-BR/ptBR_Final_Data _evaluation_EN.xlsx"  # ← Change this

TRANSLATION_PROMPT = (
    f"""Translate the following {SOURCE_LANGUAGE} text into natural English.
Preserve the original meaning, do not add interpretation, and keep the result concise and natural:
"""
)

# default model
model_name  = os.getenv("LLM_MODEL", "gpt-4o-mini")  # default: gpt-4o-mini

# ==============================
# 3) COST ESTIMATION SETTINGS (USD2EURO)
# ==============================
price_in_per_million  = 0.15
price_out_per_million = 0.60
usd_to_eur            = 0.85

# ==============================
# 4) LOAD INPUT EXCEL
# ==============================
try:
    sheets = pd.read_excel(INPUT_FILE, sheet_name=None)
except FileNotFoundError:
    print(f"Error: Input file not found at {INPUT_FILE}")
    exit()

# track token usage
token_counts = {"in": 0, "out": 0}
translated_sheets = {}

# ==============================
# 5) TRANSLATION FUNCTION
# ==============================
def translate_text(text: str) -> str:
    if pd.isna(text) or not str(text).strip():
        return text

    prompt = TRANSLATION_PROMPT + str(text).strip()

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        answer = response.choices[0].message.content.strip()

        token_counts["in"] += response.usage.prompt_tokens
        token_counts["out"] += response.usage.completion_tokens

        return answer
    
    except Exception as e:
        print(f"⚠️ Translation error, keeping original text. Detail: {e}")
        return text

# ==============================
# 6) PROCESS EACH SHEET
# ==============================
for name, df in sheets.items():

    if df is None or df.empty:
        translated_sheets[name] = df
        continue

    df_eng = df.copy()
    
    # Only translate columns exactly matching LPSgoalX_content, X = 1..15
    target_columns = [f"LPSgoal{i}_content" for i in range(1, 16) if f"LPSgoal{i}_content" in df_eng.columns]

    for col in target_columns:
        tqdm.pandas(desc=f"Translating {col} ({SOURCE_LANGUAGE} → English)")
        df_eng[col] = df_eng[col].progress_apply(translate_text)

    translated_sheets[name] = df_eng


# ==============================
# 7) SAVE OUTPUT
# ==============================
with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
    for sheet_name, df in translated_sheets.items():
        df.to_excel(writer, sheet_name=str(sheet_name)[:31], index=False)


# ==============================
# 8) COST SUMMARY
# ==============================
usd_cost = (token_counts["in"] / 1_000_000) * price_in_per_million + \
           (token_counts["out"] / 1_000_000) * price_out_per_million
eur_cost = usd_cost * usd_to_eur

print("\n===== ✅ TRANSLATION COMPLETE =====")
print(f"Source language:     {SOURCE_LANGUAGE}")
print(f"Input tokens:        {token_counts['in']}")
print(f"Output tokens:       {token_counts['out']}")
print(f"Estimated cost:      ${usd_cost:.4f}   (≈ €{eur_cost:.4f})")
print(f"Saved output to:     {OUTPUT_FILE}")