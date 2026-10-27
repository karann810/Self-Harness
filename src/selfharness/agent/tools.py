from __future__ import annotations
import fnmatch,json,subprocess
from pathlib import Path
from typing import Any
class ToolError(RuntimeError):pass
class TaskTools:
    """Four scoped tools; model-generated shell commands are never executed."""
    def __init__(self,workspace:Path,task:Any,logger:Any,docker:dict[str,Any]):self.workspace,self.task,self.logger,self.docker=workspace.resolve(),task,logger,docker
    def _path(self,value:str,write:bool=False)->Path:
        p=(self.workspace/value).resolve()
        if p!=self.workspace and self.workspace not in p.parents:raise ToolError("Path escapes task workspace")
        rel=p.relative_to(self.workspace).as_posix()
        if write and not any(fnmatch.fnmatch(rel,g) or fnmatch.fnmatch(rel,g.replace("**/","")) for g in self.task.allowed_write_paths):raise ToolError("Write denied: "+rel)
        return p
    def list_files(self,path:str=".")->str:
        base=self._path(path)
        if not base.exists():raise ToolError("Path not found")
        return "\n".join(sorted(p.relative_to(self.workspace).as_posix() for p in base.rglob("*") if p.is_file()))[:12000]
    def read_file(self,path:str)->str:
        p=self._path(path)
        if not p.is_file():raise ToolError("File not found")
        value=p.read_text(encoding="utf-8",errors="replace");return value[:20000]+("\n[truncated]" if len(value)>20000 else "")
    def write_file(self,path:str,content:str)->str:
        p=self._path(path,True);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding="utf-8");return f"Wrote {path}"
    def run_tests(self)->str:
        command=list(self.task.test_command)
        if self.docker.get("enabled",True):
            argv=["docker","run","--rm","--network","none","--cpus",str(self.docker.get("cpus",1)),"--memory",self.docker.get("memory","1g"),"--pids-limit",str(self.docker.get("pids_limit",128)),"--read-only","--tmpfs","/tmp:rw,noexec,nosuid,size=64m","-v",f"{self.workspace}:/workspace:ro","-w","/workspace",self.docker["image"],*command];cwd=None
        else:
            if not any(command[:len(pre)]==pre for pre in self.docker.get("local_allow_prefixes",[["python","-m","pytest"]])):raise ToolError("Command denied by local allowlist")
            argv,cwd=command,self.workspace
        try:result=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=self.task.timeout_seconds+(15 if cwd is None else 0),shell=False)
        except (OSError,subprocess.TimeoutExpired) as exc:raise ToolError(f"Test execution failed: {exc}") from exc
        output=(result.stdout+"\n"+result.stderr)[-8000:];self.logger.log("tests",{"command":command,"exit_code":result.returncode,"output":output})
        return json.dumps({"exit_code":result.returncode,"passed":result.returncode==0,"output":output})
