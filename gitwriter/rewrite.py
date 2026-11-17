from dataclasses import dataclass

from .models import Snapshot
from .repository import GitRepository


@dataclass(frozen=True)
class PlannedCommit:
    old_oid: str
    new_oid: str | None
    kind: str
    parents: tuple[str, ...]


def _replace_header(raw: bytes, field: str, value: str) -> bytes:
    header, _, message = raw.partition(b"\n\n")
    out = []
    found = False
    for line in header.splitlines():
        if line.startswith(field.encode() + b" "):
            out.append(field.encode() + b" " + value.encode("utf-8", "surrogateescape"))
            found = True
        else:
            out.append(line)
    if not found:
        raise ValueError(f"commit has no {field} header")
    return b"\n".join(out) + b"\n\n" + message


def _replace_message(raw: bytes, message: str) -> bytes:
    header, _, _ = raw.partition(b"\n\n")
    return header + b"\n\n" + message.encode("utf-8", "surrogateescape")


class GitWriter:
    def __init__(self, repo="."):
        self.repo = repo if isinstance(repo, GitRepository) else GitRepository(repo)

    def snapshot(self, root: str) -> Snapshot:
        resolved = self.repo.rev_parse(root)
        return Snapshot(resolved, self.repo.snapshot(resolved))

    def preview(self, plan):
        edits = {edit.commit: edit for edit in plan.edits}
        commits = {item["oid"]: item for item in self.repo.snapshot(plan.root)}
        result = []
        changed = set()
        for oid in self._topological(commits):
            item = commits[oid]
            direct = oid in edits
            descendant = any(parent in changed for parent in item["parents"])
            if direct or descendant:
                changed.add(oid)
            kind = "direct" if direct else "descendant" if descendant else "unchanged"
            result.append(
                PlannedCommit(
                    oid,
                    None,
                    kind,
                    tuple(item["parents"]),
                )
            )
        return result

    def build(self, plan):
        edits = {edit.commit: edit for edit in plan.edits}
        commits = {item["oid"]: item for item in self.repo.snapshot(plan.root)}
        mapping = {}
        for oid in self._topological(commits):
            commit = self.repo.commit(oid)
            edit = edits.get(oid)
            raw = commit.raw
            if edit:
                if (
                    edit.expected_old_value is not None
                    and getattr(commit, edit.field) != edit.expected_old_value
                ):
                    raise ValueError(f"expected {edit.field} for {oid} did not match")
                raw = (
                    _replace_message(raw, edit.new_value)
                    if edit.field == "message"
                    else _replace_header(raw, edit.field, edit.new_value)
                )
            if commit.parents:
                header, _, message = raw.partition(b"\n\n")
                lines = []
                for line in header.splitlines():
                    lines.append(
                        b"parent " + mapping[line[7:].decode()].encode()
                        if line.startswith(b"parent ")
                        else line
                    )
                raw = b"\n".join(lines) + b"\n\n" + message
            mapping[oid] = self.repo.hash_commit(raw) if raw != commit.raw else oid
        return mapping

    def verify(self, plan, mapping):
        for item in self.preview(plan):
            new = mapping[item.old_oid]
            old = self.repo.commit(item.old_oid)
            commit = self.repo.commit(new)
            if item.kind == "unchanged" and new != item.old_oid:
                raise ValueError(f"unchanged commit changed: {item.old_oid}")
            if commit.tree != old.tree:
                raise ValueError(f"tree changed: {item.old_oid}")
            if tuple(mapping[parent] for parent in item.parents) != commit.parents:
                raise ValueError(f"parent structure changed: {item.old_oid}")

    def apply(self, ref: str, plan):
        old = self.repo.rev_parse(ref)
        if old != plan.root:
            raise ValueError("plan root is not the current ref; refusing to apply")
        mapping = self.build(plan)
        self.verify(plan, mapping)
        self.repo.backup_ref(ref, old)
        self.repo.update_ref(ref, mapping[old], old)
        return mapping[old]

    @staticmethod
    def _topological(commits):
        remaining = set(commits)
        while remaining:
            ready = sorted(
                x
                for x in remaining
                if all(p not in remaining for p in commits[x]["parents"])
            )
            if not ready:
                raise ValueError("commit graph contains a cycle")
            yield from ready
            remaining.difference_update(ready)
