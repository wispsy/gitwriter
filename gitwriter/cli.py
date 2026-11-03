import argparse, json
from pathlib import Path
from .models import ProposedEdit, RewritePlan
from .rewrite import GitWriter
def main(argv=None):
 p=argparse.ArgumentParser(prog='gitwriter'); p.add_argument('--repo',default='.'); s=p.add_subparsers(dest='command',required=True)
 a=s.add_parser('snapshot'); a.add_argument('root'); a.add_argument('-o','--output',required=True)
 a=s.add_parser('propose'); a.add_argument('root'); a.add_argument('--commit',required=True); a.add_argument('--field',choices=['author','committer','message'],required=True); a.add_argument('--new-value',required=True); a.add_argument('--expected-old-value'); a.add_argument('-o','--output',required=True)
 for n in ('preview','build','verify','apply'):
  a=s.add_parser(n); a.add_argument('plan');
  if n=='verify': a.add_argument('mapping')
  if n=='apply': a.add_argument('ref')
 x=p.parse_args(argv); w=GitWriter(x.repo)
 if x.command=='snapshot': Path(x.output).write_text(w.snapshot(x.root).dumps())
 elif x.command=='propose': Path(x.output).write_text(RewritePlan(x.root,[ProposedEdit(x.commit,x.field,x.new_value,x.expected_old_value)]).dumps())
 else:
  plan=RewritePlan.loads(Path(x.plan).read_text())
  if x.command=='preview': print('\n'.join(f'{i.old_oid} {i.kind}' for i in w.preview(plan)))
  elif x.command=='build': print(json.dumps(w.build(plan),indent=2,sort_keys=True))
  elif x.command=='verify': w.verify(plan,json.loads(Path(x.mapping).read_text()))
  else: print(w.apply(x.ref,plan))
 return 0
if __name__=='__main__': main()
