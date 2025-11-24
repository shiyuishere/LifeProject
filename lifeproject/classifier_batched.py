from typing import Dict, Any
import json

# ==========================================
# Clean JSON markdown
# ==========================================
def clean_json_markdown(resp: str) -> str:
    """Remove ```json ... ``` wrapper."""
    return (
        resp.strip()
        .removeprefix("```json")
        .removesuffix("```")
        .strip()
    )

# ==========================================
# Build User Prompt (NEW - replaces old logic)
# ==========================================
def build_user_prompt(goals_dict: Dict[str, str], require_reasoning: bool) -> str:
    """
    Construct the user prompt for a single respondent.
    - Skip empty goals
    - Add reasoning request only when required
    """

    goals_text_lines = []
    for key, value in goals_dict.items():
        if value and str(value).strip() and value != "nan":
            goals_text_lines.append(f"{key}: {value}")

    goals_text = "\n".join(goals_text_lines)

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

    return (
        "The following are the life goals expressed by a person:\n\n"
        f"{goals_text}\n\n"
        f"{request}"
    )


# ==========================================
# Parse LLM output (supports both modes)
# ==========================================
def classify_text_batch(resp: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse LLM response containing multiple goals.
    Supports:
      - {"goal": {"categories": [...]}}
      - {"goal": {"categories": [...], "reasoning": "..."}}
    """
    clean_resp = clean_json_markdown(resp)
    parsed = json.loads(clean_resp)

    if isinstance(parsed, str):
        parsed = json.loads(parsed)

    if not isinstance(parsed, dict):
        raise ValueError("Parsed JSON is not a dict.")

    result = {}

    for key, value in parsed.items():

        if not isinstance(value, dict):
            raise ValueError(f"Invalid format for goal: {key}")

        categories = value.get("categories", None)
        if not categories or not isinstance(categories, list):
            raise ValueError(f"Missing or invalid `categories` for {key}")

        reasoning = value.get("reasoning", "") or ""

        result[key] = {
            "categories": categories,
            "reasoning": reasoning,
        }

    return result


# ==========================================
# Call LLM for batched classification
# ==========================================
async def get_batched_model_response(
    client,
    goals_dict: Dict[str, str],
    system_prompt: str,
    require_reasoning: bool,
    token_counts: dict,
) -> str:
    """
    Send batched prompt to the LLM.
    - Builds user prompt internally
    - Silent (no printing prompts)
    """

    # Build user prompt here
    user_prompt = build_user_prompt(goals_dict, require_reasoning)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    params = {
        "model": client.model,
        "messages": messages,
    }

    if not any(name in client.model for name in ["gpt-5"]):
        params["temperature"] = getattr(client, "temperature", 1.0)

    if hasattr(client, "max_completion_tokens") and client.max_completion_tokens:
        params["max_completion_tokens"] = client.max_completion_tokens
    elif hasattr(client, "max_tokens") and client.max_tokens:
        params["max_completion_tokens"] = client.max_tokens
    else:
        params["max_completion_tokens"] = 2000

    try:
        response = await client.client.chat.completions.create(**params)

        if hasattr(response, "usage") and response.usage:
            token_counts["in"] += getattr(response.usage, "prompt_tokens", 0)
            token_counts["out"] += getattr(response.usage, "completion_tokens", 0)

        result = response.choices[0].message.content if response.choices else "{}"

        return result or "{}"

    except Exception:
        return "{}"
