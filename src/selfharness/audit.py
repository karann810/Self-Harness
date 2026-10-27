from __future__ import annotations
import fnmatch,re
from pathlib import Path
def changed_files(before:Path,after:Path)->list[str]:
    left={p.relative_to(before).as_posix():p for p in before.rglob("*") if p.is_file()};right={p.relative_to(after).as_posix():p for p in after.rglob("*") if p.is_file()}
    return sorted(n for n in left.keys()|right.keys() if n not in left or n not in right or left[n].read_bytes()!=right[n].read_bytes())
def matches(path:str,patterns:list[str])->bool:return any(fnmatch.fnmatch(path,p) or fnmatch.fnmatch(path,p.replace("**/","")) for p in patterns)
def audit_patch(paths:list[str],workspace:Path,allowed:list[str],test_paths:list[str])->list[str]:
    flags=[]
    for rel in paths:
        if not matches(rel,allowed):flags.append("outside_allowed_paths:"+rel)
        if matches(rel,test_paths):flags.append("test_file_modified:"+rel)
        file=workspace/rel
        if file.is_file() and file.suffix==".py" and re.search(r"pytest\.skip|unittest\.skip|sys\.exit\(0\)",file.read_text(encoding="utf-8",errors="replace")):flags.append("test_bypass_pattern:"+rel)
    return sorted(set(flags))
