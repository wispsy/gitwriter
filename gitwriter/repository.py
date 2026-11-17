import os
import subprocess
from dataclasses import dataclass


class GitError(RuntimeError):
    pass


@dataclass(frozen=True)
class Commit:
    oid: str
    tree: str
    parents: tuple[str, ...]
    author: str
    committer: str
    message: str
    raw: bytes


class GitRepository:
    def __init__(self, path="."):
        self.path = os.path.abspath(path)

    def run(self, *args: str, input: bytes | None = None) -> bytes:
        process = subprocess.run(
            ["git", *args],
            cwd=self.path,
            input=input,
            capture_output=True,
            check=False,
        )
        if process.returncode:
            raise GitError(
                process.stderr.decode(errors="replace").strip() or "git failed"
            )
        return process.stdout

    def rev_parse(self, ref: str) -> str:
        return self.run("rev-parse", "--verify", ref).decode().strip()

    def commit(self, oid: str) -> Commit:
        raw = self.run("cat-file", "commit", oid)
        header, _, message = raw.partition(b"\n\n")
        fields = {}
        parents = []
        for line in header.splitlines():
            key, _, value = line.partition(b" ")
            if key == b"parent":
                parents.append(value.decode())
            elif key in (b"tree", b"author", b"committer"):
                fields[key.decode()] = value.decode()
        return Commit(
            oid,
            fields["tree"],
            tuple(parents),
            fields["author"],
            fields["committer"],
            message.decode(errors="surrogateescape").rstrip("\n"),
            raw,
        )

    def hash_commit(self, raw: bytes) -> str:
        return (
            self.run(
                "hash-object",
                "-t",
                "commit",
                "-w",
                "--stdin",
                input=raw,
            )
            .decode()
            .strip()
        )

    def update_ref(
        self,
        ref: str,
        new_oid: str,
        old_oid: str | None = None,
    ) -> None:
        arguments = [ref, new_oid]
        if old_oid:
            arguments.append(old_oid)
        self.run("update-ref", *arguments)

    def backup_ref(self, ref: str, oid: str) -> str:
        backup = f"refs/gitwriter/backup/{ref.removeprefix('refs/heads/')}"
        self.update_ref(backup, oid)
        return backup

    def snapshot(self, root: str) -> list[dict[str, object]]:
        result = []
        pending = [self.rev_parse(root)]
        seen = set()
        while pending:
            oid = pending.pop()
            if oid in seen:
                continue
            seen.add(oid)
            commit = self.commit(oid)
            result.append(
                {
                    "oid": oid,
                    "tree": commit.tree,
                    "parents": list(commit.parents),
                    "author": commit.author,
                    "committer": commit.committer,
                    "message": commit.message,
                }
            )
            pending.extend(commit.parents)
        return result
