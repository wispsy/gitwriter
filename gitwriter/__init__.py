"""Safe metadata-only Git history rewriting."""

from .models import ProposedEdit, RewritePlan, Snapshot
from .rewrite import GitWriter

__version__ = "0.1.0"
__all__ = ["GitWriter", "ProposedEdit", "RewritePlan", "Snapshot"]
