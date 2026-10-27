from __future__ import annotations
import json,re,uuid
from typing import Any
from ..agent.model import ChatModel
from ..config import ROOT
from ..events import read_jsonl,write_json
from ..models import RuleProposal
TAXONOMY=["wrong_file","misunderstood_requirement","insufficient_inspection","incomplete_fix","premature_done","did_not_run_tests","did_not_react_to_failure","tool_misuse","other"]
def classify(attempt:dict[str,Any],events:list[dict[str,Any]])->str:
    related=[e for e in events if e.get("attempt_id")==attempt["attempt_id"]]
    if attempt["status"]=="invalid_patch":return "tool_misuse"
    if not any(e.get("event")=="tests" for e in related):return "did_not_run_tests"
    return "incomplete_fix"
def diagnose(config:dict[str,Any],run_id:str)->dict[str,Any]:
    folder=ROOT/"runs"/run_id;attempts=read_jsonl(folder/"attempts.jsonl");events=read_jsonl(folder/"events.jsonl")
    failures=[a for a in attempts if a["split"]=="train" and not a["passed"]]
    if not failures:raise ValueError("No training failures in this run")
    cases=[{"task_id":a["task_id"],"category":classify(a,events),"events":[e for e in events if e.get("attempt_id")==a["attempt_id"]][-10:]} for a in failures]
    cfg=config["models"]["diagnoser"];model=ChatModel(cfg["name"],cfg["temperature"],cfg["pricing"],cfg.get("base_url"))
    prompt="Analyze only training failures. Propose one concise behavioral rule as JSON {text,rationale}. Do not request changes to tests, evaluator, tools, or data. Evidence: "+json.dumps(cases)[:30000]
    reply=model.complete([{"role":"user","content":prompt}],config["agent"]["max_completion_tokens"])
    try:raw=json.loads(reply.text)
    except json.JSONDecodeError as exc:
        found=re.search(r"\{.*\}",reply.text,re.S)
        if not found:raise ValueError("Malformed diagnoser JSON") from exc
        raw=json.loads(found.group())
    proposal=RuleProposal("rule-"+uuid.uuid4().hex[:8],str(raw["text"]).strip(),str(raw.get("rationale","")),[run_id],sorted({a["task_id"] for a in failures}))
    if not proposal.text or len(proposal.text)>500:raise ValueError("Rule text must be 1-500 characters")
    path=ROOT/"rules"/"proposals"/(proposal.rule_id+".json");write_json(path,proposal.to_dict())
    return {"proposal":proposal.to_dict(),"path":str(path),"failure_categories":{c:sum(classify(a,events)==c for a in failures) for c in TAXONOMY}}
