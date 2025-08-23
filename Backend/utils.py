from dotenv import load_dotenv
import os
import yaml
from pathlib import Path
from typing import Literal

load_dotenv()

def get_prompt(prompt_name: Literal["interviewer", "information_extractor", "information_mapper"]) -> str:
    # Default to prompts.yaml in Backend directory if PROMPT_FILE env var is not set
    prompt_file = os.getenv("PROMPT_FILE", "Backend/prompts.yaml")
    with open(Path(prompt_file), "r") as f:
        file = yaml.safe_load(f)
        return file["prompts"][prompt_name]