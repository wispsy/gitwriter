import os, subprocess
from dataclasses import dataclass
class GitError(RuntimeError): pass
@dataclass(frozen=True)
class Commit:
    oid:str; tree:str; parents:tuple[str,...]; author:str; committer:str; message:str; raw:bytes
class GitRepository:
    def __init__(self,path='.') : self.path=os.path.abspath(path)
    def run(self,*args,input=None):
        p=subprocess.run(['git',*args],cwd=self.path,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if p.returncode: raise GitError(p.stderr.decode(errors='replace').strip() or 'git failed')
        return p.stdout
    def rev_parse(self,ref): return self.run('rev-parse','--verify',ref).decode().strip()
    def commit(self,oid):
        raw=self.run('cat-file','commit',oid); header,_,message=raw.partition(b'\n\n'); fields={}; parents=[]
        for line in header.splitlines():
            key,_,value=line.partition(b' ')
            if key==b'parent': parents.append(value.decode())
            elif key in (b'tree',b'author',b'committer'): fields[key.decode()]=value.decode()
        return Commit(oid,fields['tree'],tuple(parents),fields['author'],fields['committer'],message.decode(errors='surrogateescape').rstrip('\n'),raw)
    def hash_commit(self,raw): return self.run('hash-object','-t','commit','-w','--stdin',input=raw).decode().strip()
    def update_ref(self,ref,new_oid,old_oid=None): self.run('update-ref',ref,new_oid,*(([old_oid] if old_oid else [])))
    def backup_ref(self,ref,oid):
        backup=f"refs/gitwriter/backup/{ref.removeprefix('refs/heads/')}"; self.update_ref(backup,oid); return backup
    def snapshot(self,root):
        result=[]; pending=[self.rev_parse(root)]; seen=set()
        while pending:
            oid=pending.pop()
            if oid in seen: continue
            seen.add(oid); c=self.commit(oid); result.append({'oid':oid,'tree':c.tree,'parents':list(c.parents),'author':c.author,'committer':c.committer,'message':c.message}); pending.extend(c.parents)
        return result
