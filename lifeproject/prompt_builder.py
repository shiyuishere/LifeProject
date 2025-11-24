# build system prompt from version
import os

TASKSET_DIR = "configs/prompt/taskset"
LANG_DIR = "configs/prompt/language_hint"
DEFAULT_CODEBOOK = "configs/prompt/codebook/codebook_en.txt"


def _read_text(path: str) -> str:
    """Read text file safely, return '' if not found."""
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()
    
def load_prompt(prompt_version: str, language: str = None, codebook_path: str = None):
    """
    Build system prompt according to V1-V6 rules.

    Args:
        prompt_version (str): One of ["V1", "V2", "V3", "V4", "V5", "V6"]
        language (str or None): e.g., "pt-BR", "zh-TW". Required only for V3-V6.
        codebook_language (str): Default "en". Future support for multilingual codebooks.

    Returns:
        system_prompt (str): Fully concatenated system prompt.
        require_reasoning (bool): True only for V3-V6.
    """

    # Define the components required for each version (in strict order) 
    VERSION_MAP = {
        "V1": ["role", "output_1"],
        "V2": ["role", "background", "task_intr", "code_intr", "output_1"],
        "V3": ["role", "background", "task_intr", "reasoning", "code_intr", "output_2"],
        "V4": ["language_hint", "role", "background", "task_intr", "reasoning", "code_intr", "heuristics", "output_2"],
        "V5": ["language_hint", "role", "background", "task_intr", "reasoning", "code_intr", "hard_rules", "heuristics", "output_2"],
        "V6": ["language_hint", "role", "background", "task_intr", "reasoning", "code_intr", "hard_rules", "output_2"],
        # Future versions can be added here
    }

    if prompt_version not in VERSION_MAP:
        raise ValueError(f"❌ Unsupported prompt version: {prompt_version}")

    components = VERSION_MAP[prompt_version]
    parts = []

    # Load language_hint (Only for the versions that include this component)
    if "language_hint" in components:
        if not language:
            raise ValueError(f"❌ Version {prompt_version} requires a language (e.g., --lang pt-BR)")
        lang_path = os.path.join(LANG_DIR, f"{language}.txt")
        lang_text = _read_text(lang_path)
        parts.append(lang_text)

    # Load taskset component
    for comp in components:
        if comp == "language_hint":
            continue
        file_path = os.path.join(TASKSET_DIR, f"{comp}.txt")
        parts.append(_read_text(file_path))

    # Load codebook (default English, future-proof for other languages)
    if codebook_path and os.path.exists(codebook_path):
        effective_codebook = codebook_path
    else:
        effective_codebook = DEFAULT_CODEBOOK

    codebook_text = _read_text(effective_codebook)
    parts.append(codebook_text)

    #Final concatenation (no prints!)
    system_prompt = "\n\n".join([p for p in parts if p.strip()])

    # Reasoning only for V3–V6
    require_reasoning = prompt_version in ["V3", "V4", "V5", "V6"]

    return system_prompt, require_reasoning