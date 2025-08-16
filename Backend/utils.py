from dotenv import load_dotenv
import os
import yaml
from pathlib import Path
from typing import Literal

load_dotenv()

def get_prompt(prompt_name: Literal["interviewer", "information_extractor", "information_mapper"]) -> str:
    with open(Path(os.getenv("PROMPT_FILE")), "r") as f:
        file = yaml.safe_load(f)
        return file["prompts"][prompt_name]