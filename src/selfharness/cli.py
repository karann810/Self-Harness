from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any
from .agent.runner import run_tasks
from .config import ROOT,load_config
from .datasets import dataset_hash,load_tasks,validate_dataset
from .diagnosis.propose import diagnose
from .events import read_json,read_jsonl,write_json
from .experiment import freeze_rules,run_final_test,run_round
from .eval.scoring import score

def show(value:Any)->None:print(json.dumps(value,indent=2,ensure_ascii=False))
def parser()->argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="selfharness");p.add_argument("--config",default=None);s=p.add_subparsers(dest="command",required=True)
    s.add_parser("validate-dataset")
    r=s.add_parser("run");r.add_argument("--split",choices=["train","validation"],required=True);r.add_argument("--condition",choices=["baseline","candidate"],default="baseline");r.add_argument("--rules",type=Path);r.add_argument("--repeats",type=int,default=1)
    d=s.add_parser("diagnose");d.add_argument("--run-id",required=True)
    x=s.add_parser("round");x.add_argument("--candidate",type=Path,required=True);x.add_argument("--repeats",type=int,default=3)
    f=s.add_parser("freeze-rules");f.add_argument("--note",required=True)
    t=s.add_parser("final-test");t.add_argument("--repeats",type=int,default=3);t.add_argument("--confirm-sealed",action="store_true")
    q=s.add_parser("report");q.add_argument("--run-id",required=True)
    s.add_parser("demo");return p

def demo()->dict[str,Any]:
    """Illustrative synthetic data only: no model, fixture, or test is executed."""
    baseline=[{"task_id":f"demo-{i}","seed":seed,"status":"failed_tests" if (i+seed)%3==0 else "passed","passed":(i+seed)%3!=0,"estimated_cost_usd":0,"prompt_tokens":0,"completion_tokens":0} for i in range(12) for seed in (11,23,37)]
    candidate=[dict(r,status="passed",passed=True) if r["task_id"] in {"demo-0","demo-3","demo-6"} and not r["passed"] else dict(r) for r in baseline]
    report={"synthetic_demo":True,"baseline":score(baseline),"candidate":score(candidate),"note":"Synthetic illustration only; no agent or tests were run."}
    write_json(ROOT/"runs"/"demo"/"demo-report.json",report);return report

def main(argv:list[str]|None=None)->int:
    args=parser().parse_args(argv)
    if args.command=="demo":show(demo());return 0
    config=load_config(args.config);tasks=load_tasks();errors=validate_dataset(tasks)
    if errors:show({"valid":False,"errors":errors});return 2
    if args.command=="validate-dataset":show({"valid":True,"task_count":len(tasks),"split_counts":{s:sum(t.split==s for t in tasks) for s in ("train","validation","test")},"dataset_hash":dataset_hash(tasks)});return 0
    if args.command=="run":
        chosen=[t for t in tasks if t.split==args.split];rules=[]
        if args.rules:
            raw=json.loads(args.rules.read_text(encoding="utf-8"));rules=[str(x["text"] if isinstance(x,dict) else x) for x in raw.get("rules",[raw])]
        run_id,results=run_tasks(config,chosen,args.condition,args.repeats,rules)
        write_json(ROOT/"runs"/run_id/"summary.json",{"run_id":run_id,"resolved_config":{k:v for k,v in config.items() if not k.startswith("_")},"dataset_hash":dataset_hash(tasks),"score":score([r.to_dict() for r in results])})
        show({"run_id":run_id,"score":score([r.to_dict() for r in results])});return 0
    if args.command=="diagnose":show(diagnose(config,args.run_id));return 0
    if args.command=="round":show(run_round(config,tasks,json.loads(args.candidate.read_text(encoding="utf-8")),args.repeats));return 0
    if args.command=="freeze-rules":show(freeze_rules(tasks,args.note));return 0
    if args.command=="final-test":
        if not args.confirm_sealed:print("Refusing to show sealed results; pass --confirm-sealed",file=sys.stderr);return 2
        show(run_final_test(config,tasks,args.repeats));return 0
    if args.command=="report":
        folder=ROOT/"runs"/args.run_id;gate=read_json(folder/"gate-summary.json")
        show(gate or {"run_id":args.run_id,"attempts":len(read_jsonl(folder/"attempts.jsonl")),"score":score(read_jsonl(folder/"attempts.jsonl"))});return 0
    return 2
if __name__=="__main__":raise SystemExit(main())
