from __future__ import annotations
import hashlib,json
from pathlib import Path
from .config import ROOT,project_path
from .models import Task
def tree_hash(root:Path)->str:
    digest=hashlib.sha256();skip={".git","__pycache__",".pytest_cache",".venv"}
    for file in sorted(p for p in root.rglob("*") if p.is_file() and not(set(p.relative_to(root).parts)&skip)):
        digest.update(file.relative_to(root).as_posix().encode());digest.update(b"\0");digest.update(file.read_bytes());digest.update(b"\0")
    return digest.hexdigest()
def load_tasks(path:str|Path|None=None)->list[Task]:
    file=Path(path) if path else ROOT/"data"/"tasks.jsonl"
    if not file.is_absolute():file=ROOT/file
    rows=[]
    with file.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():rows.append(Task(**json.loads(line)))
    return rows
def dataset_hash(tasks:list[Task])->str:
    digest=hashlib.sha256()
    for task in sorted(tasks,key=lambda t:t.task_id):digest.update(json.dumps(task.__dict__,sort_keys=True).encode());digest.update(tree_hash(project_path(task.repo_path)).encode())
    return digest.hexdigest()
def validate_dataset(tasks:list[Task])->list[str]:
    errors=[];ids=[t.task_id for t in tasks]
    if not tasks:errors.append("Empty task manifest")
    if len(ids)!=len(set(ids)):errors.append("Task IDs not unique")
    for task in tasks:
        root=project_path(task.repo_path)
        if not root.is_dir():errors.append(f"Missing fixture: {task.task_id}")
        elif not list(root.rglob("test_*.py")):errors.append(f"No pytest files: {task.task_id}")
        if task.split not in {"train","validation","test"}:errors.append(f"Invalid split: {task.task_id}")
    split_file=ROOT/"data"/"splits.json"
    if split_file.exists():
        declared=json.loads(split_file.read_text(encoding="utf-8"));all_ids=[i for values in declared.values() for i in values]
        if len(all_ids)!=len(set(all_ids)):errors.append("Split IDs overlap")
        for split in ("train","validation","test"):
            if {t.task_id for t in tasks if t.split==split}!=set(declared.get(split,[])):errors.append(f"{split} differs from splits.json")
    return errors
