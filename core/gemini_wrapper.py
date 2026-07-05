import json
import sys
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]

class ModernGenerativeModel:
    def __init__(self, model_name: str, system_instruction: str = None):
        from google import genai
        self.client = genai.Client(api_key=_get_api_key())
        self.model_name = model_name
        self.system_instruction = system_instruction

    def generate_content(self, contents, **kwargs):
        from google.genai import types
        
        config_args = {}
        if self.system_instruction:
            config_args["system_instruction"] = self.system_instruction
        
        config = types.GenerateContentConfig(**config_args) if config_args else None
        
        processed_contents = []
        if isinstance(contents, list):
            for item in contents:
                if isinstance(item, dict) and "mime_type" in item and "data" in item:
                    processed_contents.append(
                        types.Part.from_bytes(data=item["data"], mime_type=item["mime_type"])
                    )
                else:
                    processed_contents.append(item)
        else:
            if isinstance(contents, dict) and "mime_type" in contents and "data" in contents:
                processed_contents = [types.Part.from_bytes(data=contents["data"], mime_type=contents["mime_type"])]
            else:
                processed_contents = contents

        return self.client.models.generate_content(
            model=self.model_name,
            contents=processed_contents,
            config=config,
            **kwargs
        )
