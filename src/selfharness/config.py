from pathlib import Path
from typing import Any
import yaml
ROOT=Path(__file__).resolve().parents[2]
def load_config(path:str|Path|None=None)->dict[str,Any]:
    target=Path(path) if path else ROOT/"config"/"default.yaml"
    if not target.is_absolute():target=ROOT/target
    with target.open(encoding="utf-8") as handle:config=yaml.safe_load(handle) or {}
    config["_config_path"]=str(target.resolve());config["_project_root"]=str(ROOT);return config
def project_path(value:str|Path)->Path:
    path=Path(value);return path if path.is_absolute() else ROOT/path
