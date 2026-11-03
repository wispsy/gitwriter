import subprocess
from gitwriter import GitWriter, ProposedEdit, RewritePlan
def git(path,*args): return subprocess.check_output(['git',*args],cwd=path).decode().strip()
def test_rewrite(tmp_path):
 git(tmp_path,'init','-q'); git(tmp_path,'config','user.name','Test'); git(tmp_path,'config','user.email','test@example.com'); (tmp_path/'a').write_text('one'); git(tmp_path,'add','a'); git(tmp_path,'commit','-qm','first'); first=git(tmp_path,'rev-parse','HEAD'); (tmp_path/'a').write_text('two'); git(tmp_path,'commit','-qam','second'); second=git(tmp_path,'rev-parse','HEAD')
 w=GitWriter(tmp_path); plan=RewritePlan(second,[ProposedEdit(first,'message','renamed','first')]); assert [x.kind for x in w.preview(plan)]==['direct','descendant']; m=w.build(plan); w.verify(plan,m); assert w.repo.commit(m[first]).tree==w.repo.commit(first).tree; assert w.repo.commit(m[second]).parents==(m[first],)
def test_apply_backup(tmp_path):
 git(tmp_path,'init','-q'); git(tmp_path,'config','user.name','Test'); git(tmp_path,'config','user.email','test@example.com'); (tmp_path/'a').write_text('x'); git(tmp_path,'add','a'); git(tmp_path,'commit','-qm','old'); old=git(tmp_path,'rev-parse','HEAD'); w=GitWriter(tmp_path); new=w.apply('HEAD',RewritePlan(old,[ProposedEdit(old,'message','new','old')])); assert git(tmp_path,'log','-1','--format=%s')=='new'; assert git(tmp_path,'rev-parse','refs/gitwriter/backup/HEAD')==old; assert new!=old
