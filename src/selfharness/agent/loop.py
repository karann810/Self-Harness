from __future__ import annotations
import json,re
from pathlib import Path
from typing import Any
from .model import ChatModel
from .tools import TaskTools,ToolError
SYSTEM="""You are a careful coding agent in an isolated task repo. Inspect before editing; make a focused change; run tests after edits; only report completion after tests pass. Follow rules without violating tool policy.
Accepted rules:
{rules}
Tools: list_files(path='.'), read_file(path), write_file(path,content), run_tests().
Respond with one JSON object per turn, without markdown fences:
{{"tool":"read_file","arguments":{{"path":"src/core.py"}}}}
{{"tool":"write_file","arguments":{{"path":"src/core.py","content":"..."}}}}
{{"done":true,"summary":"..."}}
"""
def parse_action(text:str)->dict[str,Any]:
    try:value=json.loads(text.strip())
    except json.JSONDecodeError:
        match=re.search(r"\{.*\}",text,re.S)
        if not match:raise ValueError("No JSON action found")
        value=json.loads(match.group())
    if not isinstance(value,dict):raise ValueError("Action must be an object")
    return value
class AgentLoop:
    def __init__(self,model:ChatModel,limits:dict[str,Any],docker:dict[str,Any]):self.model,self.limits,self.docker=model,limits,docker
    def run(self,task:Any,workspace:Path,rules:list[str],logger:Any)->dict[str,Any]:
        messages=[{"role":"system","content":SYSTEM.format(rules="\n".join("- "+r for r in rules) or "(none)")},{"role":"user","content":task.instruction}]
        tools=TaskTools(workspace,task,logger,self.docker);handlers={"list_files":tools.list_files,"read_file":tools.read_file,"write_file":tools.write_file,"run_tests":tools.run_tests}
        state={"steps":0,"passed":False,"prompt_tokens":0,"completion_tokens":0}
        for step in range(int(self.limits["max_steps"])):
            state["steps"]=step+1;reply=None
            try:
                reply=self.model.complete(messages,int(self.limits["max_completion_tokens"]))
                state["prompt_tokens"]+=reply.prompt_tokens;state["completion_tokens"]+=reply.completion_tokens
                logger.log("model_response",{"step":step+1,"text":reply.text,"prompt_tokens":reply.prompt_tokens,"completion_tokens":reply.completion_tokens})
                action=parse_action(reply.text)
            except Exception as exc:
                logger.log("model_or_parse_error",{"step":step+1,"error":str(exc)[:1000]})
                messages.extend([{"role":"assistant","content":reply.text if reply else ""},{"role":"user","content":"Return one valid JSON action using an available tool."}]);continue
            if action.get("done") is True:break
            name,args=action.get("tool"),action.get("arguments",{})
            try:
                if name not in handlers or not isinstance(args,dict):raise ToolError("Unknown tool or malformed arguments")
                result=handlers[name](**args)
            except (TypeError,ToolError,OSError) as exc:result="Tool error: "+str(exc)
            logger.log("tool_result",{"step":step+1,"tool":name,"result":str(result)[:8000]})
            if name=="run_tests":
                try:state["passed"]=bool(json.loads(result).get("passed"))
                except (ValueError,AttributeError):pass
            messages.extend([{"role":"assistant","content":reply.text},{"role":"user","content":"Tool result: "+str(result)}])
        return state
