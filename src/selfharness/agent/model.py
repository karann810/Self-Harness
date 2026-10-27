from __future__ import annotations
import json,os
from dataclasses import dataclass
from typing import Any
@dataclass
class Reply:text:str;prompt_tokens:int;completion_tokens:int
class ChatModel:
    """OpenAI-compatible adapter, imported lazily for offline CLI commands."""
    def __init__(self,name:str,temperature:float,pricing:dict[str,float],base_url:str|None=None):self.name,self.temperature,self.pricing,self.base_url=name,temperature,pricing,base_url;self.client=None
    def _get(self):
        if self.client is None:
            from openai import OpenAI
            key=os.getenv("OPENAI_API_KEY")
            if not key:raise RuntimeError("Set OPENAI_API_KEY for model-backed runs")
            kwargs={"api_key":key}
            if self.base_url:kwargs["base_url"]=self.base_url
            self.client=OpenAI(**kwargs)
        return self.client
    def complete(self,messages:list[dict[str,str]],max_tokens:int)->Reply:
        response=self._get().chat.completions.create(model=self.name,messages=messages,temperature=self.temperature,max_tokens=max_tokens)
        usage=response.usage
        return Reply(response.choices[0].message.content or "",usage.prompt_tokens if usage else 0,usage.completion_tokens if usage else 0)
    def estimated_cost(self,prompt:int,completion:int)->float:return (prompt*self.pricing.get("input_per_million_usd",0)+completion*self.pricing.get("output_per_million_usd",0))/1_000_000
