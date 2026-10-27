from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
from .config import ROOT
from .agent.runner import run_tasks
from .datasets import dataset_hash
from .events import append_jsonl,read_json,write_json
from .eval.scoring import gate_decision,score

def accepted()->dict[str,Any]:return read_json(ROOT/"rules"/"accepted.json",{"version":0,"rules":[]})
def run_round(config:dict[str,Any],tasks:list[Any],candidate:dict[str,Any],repeats:int)->dict[str,Any]:
    if (ROOT/"state"/"freeze.json").exists():raise RuntimeError("Rules frozen; start a fresh experiment to tune further")
    validation=[t for t in tasks if t.split=="validation"]
    old=accepted();base_rules=[r["text"] for r in old["rules"]]
    base_id,base=run_tasks(config,validation,"baseline",repeats,base_rules)
    cand_id,cand=run_tasks(config,validation,"candidate",repeats,base_rules+[candidate["text"]])
    policy=config["gate"];prefixes=tuple(policy["critical_audit_prefixes"])
    flags=sorted({f for row in base+cand for f in row.audit_flags if f.startswith(prefixes)})
    report=gate_decision([r.to_dict() for r in base],[r.to_dict() for r in cand],policy,flags)
    report.update({"baseline_run_id":base_id,"candidate_run_id":cand_id,"candidate_rule_id":candidate.get("rule_id"),"dataset_hash":dataset_hash(tasks),"accepted_rules_version":old["version"]})
    append_jsonl(ROOT/"runs"/cand_id/"gate.jsonl",{"candidate":candidate,"report":report})
    if report["decision"]=="accepted":
        old["version"]+=1;old["rules"].append(candidate);write_json(ROOT/"rules"/"accepted.json",old)
    write_json(ROOT/"runs"/cand_id/"gate-summary.json",report);return report

def freeze_rules(tasks:list[Any],note:str)->dict[str,Any]:
    path=ROOT/"state"/"freeze.json"
    if path.exists():raise RuntimeError("Rules already frozen")
    rules=accepted();record={"note":note,"rules_hash":hashlib.sha256(json.dumps(rules,sort_keys=True).encode()).hexdigest(),"dataset_hash":dataset_hash(tasks)}
    write_json(path,record);return record

def run_final_test(config:dict[str,Any],tasks:list[Any],repeats:int)->dict[str,Any]:
    frozen=read_json(ROOT/"state"/"freeze.json");rules=accepted()
    if not frozen:raise RuntimeError("Freeze rules before final test")
    digest=hashlib.sha256(json.dumps(rules,sort_keys=True).encode()).hexdigest()
    if digest!=frozen["rules_hash"]:raise RuntimeError("Rules changed after freeze")
    selected=[t for t in tasks if t.split=="test"]
    run_id,results=run_tasks(config,selected,"final_frozen",repeats,[r["text"] for r in rules["rules"]])
    report={"run_id":run_id,"freeze":frozen,"dataset_hash":dataset_hash(tasks),"score":score([r.to_dict() for r in results]),"results":[r.to_dict() for r in results]}
    write_json(ROOT/"runs"/run_id/"final-report.json",report);return report
