# gitwriter

`gitwriter` 0.1.0 safely rewrites Git commit metadata without touching trees or changing commit parent/merge structure. It invokes the installed `git` executable through `subprocess`.

```python
from gitwriter import GitWriter, ProposedEdit, RewritePlan
w = GitWriter('.')
root = w.snapshot('main').root
plan = RewritePlan(root, [ProposedEdit(commit, 'author', 'New Name <new@example.com>', expected_old_value='Old Name <old@example.com>')])
w.verify(plan, w.build(plan)); w.apply('main', plan)
```

The CLI exposes `snapshot`, `propose`, `preview`, `build`, `verify`, and `apply`. Snapshots and plans are versioned JSON with one tabular-friendly record per commit. `preview` distinguishes unchanged, direct, and descendant rebuilds.

Every edit may provide an expected-old-value reference; mismatches abort. `apply` requires the plan root to match the current ref, verifies trees and parent/merge ordering, and creates `refs/gitwriter/backup/<ref>` before compare-and-swap updating the ref. Working-tree files are never edited.

Changing author, committer, or message invalidates commit IDs and cryptographic signatures (including signed/tagged-history trust); review and re-sign as needed. Descendants are rebuilt only to update parent IDs, with other metadata copied byte-for-byte.

Snapshots record metadata and object IDs, not file objects. They cannot restore missing file objects and are not a repository backup; retain a normal Git backup or clone.
