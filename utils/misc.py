import json

def get_text(key: str) -> str:
    with open("locale/ru.json", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(key, f"!{key}!")
