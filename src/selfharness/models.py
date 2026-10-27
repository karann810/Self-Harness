from __future__ import annotations
from dataclasses import asdict,dataclass,field
from typing import Any,Literal
Status=Literal["passed","failed_tests","budget_exhausted","model_error","sandbox_error","tool_error","invalid_patch"]
@dataclass(frozen=True)
class Task:
    task_id:str;split:str;repo_path:str;instruction:str;test_command:list[str]
    timeout_seconds:int=60;allowed_write_paths:list[str]=field(default_factory=lambda:["src/**"])
    test_paths:list[str]=field(default_factory=lambda:["tests/**"]);tags:list[str]=field(default_factory=list);difficulty:int=1
@dataclass
class AttemptResult:
    run_id:str;attempt_id:str;task_id:str;split:str;condition:str;seed:int;status:Status;passed:bool;exit_code:int|None;steps:int;duration_seconds:float
    prompt_tokens:int=0;completion_tokens:int=0;estimated_cost_usd:float=0.;patch_hash:str="";changed_paths:list[str]=field(default_factory=list);audit_flags:list[str]=field(default_factory=list);test_output_excerpt:str="";error:str|None=None
    def to_dict(self)->dict[str,Any]:return asdict(self)
@dataclass(frozen=True)
class RuleProposal:
    rule_id:str;text:str;rationale:str;source_run_ids:list[str];source_task_ids:list[str]
    def to_dict(self)->dict[str,Any]:return asdict(self)
