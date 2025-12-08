# utils/config_loader.py
import yaml
import os


def load_yaml(path):
    if not os.path.exists(path):
        return {}  # évite les erreurs si le fichier n’existe pas encore

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_yaml(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

