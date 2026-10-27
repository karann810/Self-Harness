from __future__ import annotations
import random
from typing import Any
from scipy.stats import binomtest

def score(rows:list[dict[str,Any]])->dict[str,Any]:
    valid=[r for r in rows if r["status"] in {"passed","failed_tests"}];wins=sum(bool(r["passed"]) for r in valid)
    return {"successes":wins,"attempts":len(valid),"pass_rate":wins/len(valid) if valid else None,"invalid_or_error_attempts":len(rows)-len(valid),"cost_usd":sum(float(r.get("estimated_cost_usd",0)) for r in rows),"tokens":sum(int(r.get("prompt_tokens",0))+int(r.get("completion_tokens",0)) for r in rows)}
def paired_deltas(base:list[dict[str,Any]],candidate:list[dict[str,Any]])->tuple[list[int],list[dict[str,Any]]]:
    def index(rows):
        result={}
        for row in rows:
            if row["status"] not in {"passed","failed_tests"}:continue
            key=(row["task_id"],int(row["seed"]))
            if key in result:raise ValueError("Duplicate valid task/seed outcome: "+str(key))
            result[key]=row
        return result
    left,right=index(base),index(candidate);pairs=[]
    for task,seed in sorted(left.keys()&right.keys()):pairs.append({"task_id":task,"seed":seed,"baseline_passed":bool(left[(task,seed)]["passed"]),"candidate_passed":bool(right[(task,seed)]["passed"])})
    return [int(p["candidate_passed"])-int(p["baseline_passed"]) for p in pairs],pairs
def paired_bootstrap(deltas:list[int],confidence:float=.95,samples:int=10000,seed:int=1729)->dict[str,float|None]:
    if not deltas:return {"mean":None,"lower":None,"upper":None}
    rng=random.Random(seed);means=sorted(sum(rng.choices(deltas,k=len(deltas)))/len(deltas) for _ in range(samples));alpha=1-confidence
    return {"mean":sum(deltas)/len(deltas),"lower":means[int(alpha/2*samples)],"upper":means[min(samples-1,int((1-alpha/2)*samples))]}
def gate_decision(base:list[dict[str,Any]],candidate:list[dict[str,Any]],policy:dict[str,Any],flags:list[str]|None=None)->dict[str,Any]:
    deltas,pairs=paired_deltas(base,candidate);interval=paired_bootstrap(deltas,policy["confidence"],policy["bootstrap_samples"],policy["bootstrap_seed"])
    seeds={}
    for pair,delta in zip(pairs,deltas):seeds.setdefault(pair["seed"],[]).append(delta)
    seed_delta={str(seed):sum(v)/len(v) for seed,v in seeds.items()};flags=flags or []
    enough=len(pairs)>=policy["minimum_pairs"];improves=interval["lower"] is not None and interval["lower"]>=policy["minimum_improvement"]
    regressed=any(v < -policy["maximum_seed_regression"] for v in seed_delta.values())
    if not enough:decision,reason="inconclusive","too_few_valid_pairs"
    elif flags:decision,reason="rejected","critical_audit_flags"
    elif regressed:decision,reason="rejected","seed_regression_guardrail"
    elif improves:decision,reason="accepted","paired_lower_bound_clears_threshold"
    else:decision,reason="inconclusive","improvement_not_established"
    wins=sum(not p["baseline_passed"] and p["candidate_passed"] for p in pairs);losses=sum(p["baseline_passed"] and not p["candidate_passed"] for p in pairs);discordant=wins+losses
    return {"decision":decision,"reason":reason,"pairs":len(pairs),"paired_delta":interval,"seed_paired_deltas":seed_delta,"paired_outcomes":{"candidate_only_wins":wins,"baseline_only_wins":losses,"mcnemar_exact_pvalue":float(binomtest(wins,discordant).pvalue) if discordant else 1.0},"baseline":score(base),"candidate":score(candidate),"critical_audit_flags":flags,"per_task_pairs":pairs,"policy":policy}
