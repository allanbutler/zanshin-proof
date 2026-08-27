"""Zanshin Proof public package interface."""

from zanshin_proof.evaluator import evaluate
from zanshin_proof.policy import load_policy

__all__ = ["evaluate", "load_policy"]
__version__ = "0.1.0"
