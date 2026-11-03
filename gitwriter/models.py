from dataclasses import dataclass, field
from typing import Any, Literal
import json
VERSION=1
EditField=Literal["author","committer","message"]
@dataclass(frozen=True)
class ProposedEdit:
    commit:str; field:EditField; new_value:str; expected_old_value:str|None=None
    def to_dict(self): return {"commit":self.commit,"field":self.field,"new_value":self.new_value,"expected_old_value":self.expected_old_value}
    @classmethod
    def from_dict(cls,d): return cls(d["commit"],d["field"],d["new_value"],d.get("expected_old_value"))
@dataclass(frozen=True)
class Snapshot:
    root:str; commits:list[dict[str,Any]]; version:int=VERSION
    def dumps(self): return json.dumps({"version":self.version,"root":self.root,"commits":self.commits},indent=2,sort_keys=True)+"\n"
    @classmethod
    def loads(cls,s):
        d=json.loads(s)
        if d.get("version")!=VERSION: raise ValueError(f"unsupported snapshot version: {d.get('version')}")
        return cls(d["root"],d["commits"],d["version"])
@dataclass(frozen=True)
class RewritePlan:
    root:str; edits:list[ProposedEdit]=field(default_factory=list); version:int=VERSION
    def dumps(self): return json.dumps({"version":self.version,"root":self.root,"edits":[e.to_dict() for e in self.edits]},indent=2,sort_keys=True)+"\n"
    @classmethod
    def loads(cls,s):
        d=json.loads(s)
        if d.get("version")!=VERSION: raise ValueError(f"unsupported plan version: {d.get('version')}")
        return cls(d["root"],[ProposedEdit.from_dict(e) for e in d["edits"]],d["version"])
