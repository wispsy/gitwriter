import json
from dataclasses import dataclass, field
from typing import Any, Literal

VERSION = 1
EditField = Literal["author", "committer", "message"]


@dataclass(frozen=True)
class ProposedEdit:
    commit: str
    field: EditField
    new_value: str
    expected_old_value: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "commit": self.commit,
            "field": self.field,
            "new_value": self.new_value,
            "expected_old_value": self.expected_old_value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProposedEdit":
        return cls(
            data["commit"],
            data["field"],
            data["new_value"],
            data.get("expected_old_value"),
        )


@dataclass(frozen=True)
class Snapshot:
    root: str
    commits: list[dict[str, Any]]
    version: int = VERSION

    def dumps(self) -> str:
        return (
            json.dumps(
                {"version": self.version, "root": self.root, "commits": self.commits},
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    @classmethod
    def loads(cls, text: str) -> "Snapshot":
        data = json.loads(text)
        if data.get("version") != VERSION:
            raise ValueError(f"unsupported snapshot version: {data.get('version')}")
        return cls(data["root"], data["commits"], data["version"])


@dataclass(frozen=True)
class RewritePlan:
    root: str
    edits: list[ProposedEdit] = field(default_factory=list)
    version: int = VERSION

    def dumps(self) -> str:
        return (
            json.dumps(
                {
                    "version": self.version,
                    "root": self.root,
                    "edits": [edit.to_dict() for edit in self.edits],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    @classmethod
    def loads(cls, text: str) -> "RewritePlan":
        data = json.loads(text)
        if data.get("version") != VERSION:
            raise ValueError(f"unsupported plan version: {data.get('version')}")
        return cls(
            data["root"],
            [ProposedEdit.from_dict(edit) for edit in data["edits"]],
            data["version"],
        )
