import os
import json
from typing import Any, Dict

CONFIG_DIR = ".x1ayu_rag"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> Dict[str, Any]:
    ensure_config_dir()
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg: Dict[str, Any]) -> None:
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def update_config(values: Dict[str, Any]) -> Dict[str, Any]:
    def _merge(dst: Dict[str, Any], src: Dict[str, Any]):
        for k, v in src.items():
            if v is None:
                continue
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                _merge(dst[k], v)
            else:
                dst[k] = v
    cfg = load_config()
    _merge(cfg, values or {})
    save_config(cfg)
    return cfg
