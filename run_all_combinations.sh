#!/bin/bash

echo "🚀 Starting full parameter sweep (60 combinations)..."

SUMMARY_FILE="output/run_summary.csv"
mkdir -p output

# Write CSV header
echo "run_id,input,taskset,language,model,mark,token_in,token_out,price_in,price_out,estimated_cost_usd" > "$SUMMARY_FILE"

INPUTS=(
    "input/pt-BR/ptBR_Final_Data_classification.xlsx"
    # "input/ZH/ZH Data_classification.xlsx"
)

TASKSETS=(
    "configs/prompt/taskset/V1.yaml"
    "configs/prompt/taskset/V2.yaml"
    "configs/prompt/taskset/V3.yaml"
    # "configs/prompt/taskset/V4.yaml"
    "configs/prompt/taskset/V5.yaml"
)

LANGUAGES=(
    "configs/prompt/language_hint/pt-BR.yaml"
    # "configs/prompt/language_hint/zh-TW.yaml"
)

MODELS=(
    # "configs/llms/openai/G4O-mini.yaml"
    # "configs/llms/openai/G5.yaml"
    "configs/llms/openai/G41-mini.yaml"
)

COUNT=0

for INPUT in "${INPUTS[@]}"; do
  for TS in "${TASKSETS[@]}"; do
    for LANG in "${LANGUAGES[@]}"; do
      for MODEL in "${MODELS[@]}"; do

        COUNT=$((COUNT+1))

        echo "======================================"
        echo "▶ Run $COUNT / 4"
        echo "INPUT    = $INPUT"
        echo "TASKSET  = $TS"
        echo "LANG     = $LANG"
        echo "MODEL    = $MODEL"
        echo "======================================"

        # Extract model mark & pricing info from YAML
        mark=$(grep -E '^mark:' "$MODEL" | awk '{print $2}')
        price_in=$(grep -E '^price_input_per_million:' "$MODEL" | awk '{print $2}')
        price_out=$(grep -E '^price_output_per_million:' "$MODEL" | awk '{print $2}')

        # Capture JSON output from main.py
        JSON_OUTPUT=$(uv run python main.py \
            --input "$INPUT" \
            --taskset "$TS" \
            --language "$LANG" \
            --model "$MODEL" \
            | tail -n 1)

        # Parse token counts from JSON
        token_in=$(echo "$JSON_OUTPUT"   | python3 -c "import sys, json; print(json.load(sys.stdin)['token_in'])")
        token_out=$(echo "$JSON_OUTPUT"  | python3 -c "import sys, json; print(json.load(sys.stdin)['token_out'])")

        # Compute estimated cost in USD
        cost=$(echo "scale=6; ($token_in / 1000000) * $price_in + ($token_out / 1000000) * $price_out" | bc)

        echo "Model mark: $mark"
        echo "Token in:   $token_in"
        echo "Token out:  $token_out"
        echo "Cost (USD): \$${cost}"

        # Append CSV row
        echo "$COUNT,$INPUT,$TS,$LANG,$MODEL,$mark,$token_in,$token_out,$price_in,$price_out,$cost" >> "$SUMMARY_FILE"

      done
    done
  done
done

echo "🎉 Finished! Summary saved to $SUMMARY_FILE"
