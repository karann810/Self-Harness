from __future__ import annotations
import hashlib,json,shutil,tempfile,time,uuid
from pathlib import Path
from typing import Any
from ..audit import audit_patch,changed_files
from ..config import ROOT,project_path
from ..datasets import tree_hash
from ..events import EventLogger,append_jsonl
from ..models import AttemptResult
from .loop import AgentLoop
from .model import ChatModel

def new_run_id()->str:return time.strftime("%Y%m%dT%H%M%SZ",time.gmtime())+"_"+uuid.uuid4().hex[:6]
class AttemptRunner:
    def __init__(self,config:dict[str,Any],run_id:str):
        self.config,self.run_id=config,run_id;model=config["models"]["agent"]
        self.chat=ChatModel(model["name"],model["temperature"],model["pricing"],model.get("base_url"));self.loop=AgentLoop(self.chat,config["agent"],config["docker"])
        self.directory=ROOT/"runs"/run_id;self.directory.mkdir(parents=True,exist_ok=True)
    def one(self,task:Any,condition:str,seed:int,rules:list[str])->AttemptResult:
        attempt=uuid.uuid4().hex[:12];logger=EventLogger(self.directory/"events.jsonl",self.run_id,attempt,task.task_id);start=time.monotonic()
        state={"steps":0,"passed":False,"prompt_tokens":0,"completion_tokens":0};paths=[];flags=[];err=None;output="";exit_code=None;patch="";status="model_error"
        try:
            fixture=project_path(task.repo_path)
            with tempfile.TemporaryDirectory(prefix="selfharness-") as tmp:
                workspace=Path(tmp)/task.task_id;shutil.copytree(fixture,workspace,ignore=shutil.ignore_patterns(".git","__pycache__",".pytest_cache"))
                fixture_digest=tree_hash(workspace);logger.log("attempt_started",{"condition":condition,"seed":seed,"fixture_hash":fixture_digest,"rule_count":len(rules)})
                state=self.loop.run(task,workspace,rules,logger);paths=changed_files(fixture,workspace);flags=audit_patch(paths,workspace,task.allowed_write_paths,task.test_paths)
                for line in reversed((self.directory/"events.jsonl").read_text(encoding="utf-8").splitlines()):
                    event=json.loads(line)
                    if event.get("attempt_id")==attempt and event.get("event")=="tests":exit_code=event["payload"]["exit_code"];output=event["payload"]["output"][-1000:];break
                status="invalid_patch" if flags else ("passed" if state["passed"] else "failed_tests")
                patch=hashlib.sha256((fixture_digest+"\n"+"\n".join(paths)).encode()).hexdigest()
        except Exception as exc:
            err=f"{type(exc).__name__}: {exc}"[:2000];status="sandbox_error" if "docker" in str(exc).lower() else "model_error";logger.log("attempt_error",{"error":err})
        prices=self.config["models"]["agent"]["pricing"];cost=(state["prompt_tokens"]*prices["input_per_million_usd"]+state["completion_tokens"]*prices["output_per_million_usd"])/1_000_000
        result=AttemptResult(self.run_id,attempt,task.task_id,task.split,condition,seed,status,bool(state["passed"] and not flags),exit_code,state["steps"],time.monotonic()-start,state["prompt_tokens"],state["completion_tokens"],cost,patch,paths,flags,output,err)
        append_jsonl(self.directory/"attempts.jsonl",result.to_dict());return result

def run_tasks(config:dict[str,Any],tasks:list[Any],condition:str,repeats:int,rules:list[str],run_id:str|None=None)->tuple[str,list[AttemptResult]]:
    run_id=run_id or new_run_id();runner=AttemptRunner(config,run_id);results=[];seeds=list(config["evaluation"]["seeds"])
    while len(seeds)<repeats:seeds.append(max(seeds,default=0)+1)
    for seed in seeds[:repeats]:
        for task in tasks:results.append(runner.one(task,condition,int(seed),rules))
    return run_id,results
