import os
import re
import yaml
from dotenv import load_dotenv
from openai import AsyncOpenAI
from .llm import LLMConfig

load_dotenv()


class LLMConfigManager:
    """
    Factory for creating LLMConfig instances for different LLM providers.
    Supports both environment-based (.env) and YAML-based configuration.
    """

    # === YAML-based config ===
    @staticmethod
    def from_yaml(yaml_path: str) -> LLMConfig:
        """
        Load model configuration from a YAML file (e.g. configs/llms/openai/G5.yaml).

        Example YAML:
        ---
        provider: "openai"
        base_url: "https://api.openai.com/v1"
        api_key: "${OPENAI_API_KEY}"
        model: "gpt-4o-mini"
        temperature: 0.0
        concurrency: 5
        input_price: 0.15
        output_price: 0.60
        """

        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Model config not found: {yaml_path}")

        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # --- Extract basic fields ---
        provider = data.get("provider", "openai")
        base_url = data.get("base_url", "https://api.openai.com/v1")
        model = data.get("model", "gpt-4o-mini")
        temperature = data.get("temperature", 0.0)

        # --- ✅ Handle ${ENV_VAR} substitution ---
        raw_key = data.get("api_key", "")
        if isinstance(raw_key, str) and raw_key.startswith("${") and raw_key.endswith("}"):
            env_var = re.findall(r"\${(.*?)}", raw_key)[0]
            api_key = os.getenv(env_var, "")
            if not api_key:
                raise ValueError(f"⚠️ Environment variable {env_var} not found for API key.")
        else:
            api_key = raw_key or os.getenv("OPENAI_API_KEY", "")

        # --- Optional fields ---
        headers = data.get("headers", {})
        max_completion_tokens = data.get("max_completion_tokens", None)
        concurrency = data.get("concurrency", 1)
        input_price = data.get("input_price", None)
        output_price = data.get("output_price", None)
        mark = data.get("mark", None)

        # --- Create config object ---
        config = LLMConfig(
            base_url=base_url,
            api_key=api_key,
            model=model,
            temperature=temperature,
            headers=headers,
        )

        # Attach metadata (for logging or subsequent calculations)
        config.max_completion_tokens = max_completion_tokens
        config.concurrency = concurrency
        config.input_price = input_price
        config.output_price = output_price
        config.mark = mark

        # --- Initialize AsyncOpenAI client ---
        config.client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
            default_headers=config.headers,
            timeout=200.0,
        )

        print(f"✅ Loaded model config from YAML: {yaml_path}")
        return config
