"""Structural checks on the Alembic revision chain.

Static introspection only — no engine, no DATABASE_URL, no upgrade/downgrade
run. The production database is a shared remote Supabase instance, so actually
executing migrations here is not an option.
"""

import ast
import inspect
import textwrap
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _is_noop(func) -> bool:
    """True if the function body is only a docstring and/or `pass`.

    Uses ast rather than string matching so a one-line docstring
    (`\"\"\"nothing to do\"\"\"`) is correctly recognised as no-op.
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    body = tree.body[0].body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]  # drop the docstring
    return all(isinstance(node, ast.Pass) for node in body)


@pytest.fixture(scope="module")
def script_dir() -> ScriptDirectory:
    cfg = Config()
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return ScriptDirectory.from_config(cfg)


@pytest.fixture(scope="module")
def revisions(script_dir):
    return list(script_dir.walk_revisions())


def test_there_is_exactly_one_head(script_dir):
    """Two heads means a branched history: `alembic upgrade head` would fail."""
    heads = script_dir.get_heads()
    assert len(heads) == 1, f"migration history has forked: {heads}"


def test_there_is_exactly_one_base(script_dir):
    assert len(script_dir.get_bases()) == 1


def test_the_chain_is_unbroken(script_dir, revisions):
    """Every down_revision must name a revision that exists."""
    known = {rev.revision for rev in revisions}
    for rev in revisions:
        if rev.down_revision is None:
            continue
        parents = (
            rev.down_revision
            if isinstance(rev.down_revision, tuple)
            else (rev.down_revision,)
        )
        for parent in parents:
            assert parent in known, (
                f"revision {rev.revision} points at missing parent {parent}"
            )


def test_every_revision_walks_back_to_the_base(script_dir):
    """Traversing from head to base must reach every revision exactly once."""
    head = script_dir.get_current_head()
    walked = list(script_dir.iterate_revisions(head, "base"))
    assert len(walked) == len(list(script_dir.walk_revisions()))


def test_every_revision_defines_upgrade_and_downgrade(revisions):
    for rev in revisions:
        module = rev.module
        assert callable(getattr(module, "upgrade", None)), f"{rev.revision}: no upgrade()"
        assert callable(getattr(module, "downgrade", None)), f"{rev.revision}: no downgrade()"


def test_noop_detector_actually_detects_a_noop():
    """Guard against the check below silently passing on everything."""

    def empty():
        pass

    def docstring_only():
        """nothing to do"""

    def docstring_then_pass():
        """nothing to do"""
        pass

    def real():
        op.drop_table("x")  # noqa: F821

    assert _is_noop(empty)
    assert _is_noop(docstring_only)
    assert _is_noop(docstring_then_pass)
    assert not _is_noop(real)


def test_no_downgrade_is_a_silent_no_op(revisions):
    """A `pass`-only downgrade makes a rollback silently corrupt the schema."""
    offenders = [rev.revision for rev in revisions if _is_noop(rev.module.downgrade)]
    assert not offenders, f"revisions with an empty downgrade(): {offenders}"


def test_no_upgrade_is_a_silent_no_op(revisions):
    offenders = [rev.revision for rev in revisions if _is_noop(rev.module.upgrade)]
    assert not offenders, f"revisions with an empty upgrade(): {offenders}"
