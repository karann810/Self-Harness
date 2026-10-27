import json
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
def utc_now()->str:return datetime.now(timezone.utc).isoformat()
def append_jsonl(path:str|Path,record:dict[str,Any])->None:
    target=Path(path);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("a",encoding="utf-8",newline="\n") as handle:handle.write(json.dumps(record,ensure_ascii=False,sort_keys=True)+"\n")
def read_jsonl(path:str|Path)->list[dict[str,Any]]:
    target=Path(path)
    if not target.exists():return []
    return [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
def write_json(path:str|Path,value:Any)->None:
    target=Path(path);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def read_json(path:str|Path,default:Any=None)->Any:
    target=Path(path);return json.loads(target.read_text(encoding="utf-8")) if target.exists() else default
class EventLogger:
    def __init__(self,path:str|Path,run_id:str,attempt_id:str,task_id:str):self.path,self.run_id,self.attempt_id,self.task_id=Path(path),run_id,attempt_id,task_id
    def log(self,event:str,payload:dict[str,Any])->None:append_jsonl(self.path,{"run_id":self.run_id,"attempt_id":self.attempt_id,"task_id":self.task_id,"timestamp":utc_now(),"event":event,"payload":payload})
