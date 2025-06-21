"""
Collaboration module for STPA Tool
Handles branching, merging, and multi-user collaboration features.
"""

from .branch_manager import BranchManager
from .merge_manager import MergeManager

__all__ = ['BranchManager', 'MergeManager']