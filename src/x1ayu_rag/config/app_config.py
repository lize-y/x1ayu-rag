import os
import json
from typing import Any, Dict

CONFIG_DIR = ".x1ayu_rag"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def ensure_config_dir():
    """确保配置目录存在。"""
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """加载配置文件。
    
    返回:
        Dict[str, Any]: 配置字典，如果加载失败则返回空字典。
    """
    ensure_config_dir()
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg: Dict[str, Any]) -> None:
    """保存配置到文件。
    
    参数:
        cfg: 要保存的配置字典。
    """
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def update_config(values: Dict[str, Any]) -> Dict[str, Any]:
    """更新配置。
    
    合并新值到现有配置中。
    
    参数:
        values: 要更新的配置值。
        
    返回:
        Dict[str, Any]: 更新后的完整配置。
    """
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
