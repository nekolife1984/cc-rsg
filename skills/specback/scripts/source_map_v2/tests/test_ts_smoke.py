"""Tree-sitter install smoke tests (Issue #123).

Verifies that every tree-sitter backed language loads with the currently
installed grammar versions.  This catches the silent-extractor-disablement
failure mode where ``pip install -r requirements.txt`` succeeds but
``tshelpers.have(lang)`` is False because a grammar's Language version no
longer matches the installed core (e.g. tree-sitter-python 0.25.x ships
Language version 15 while core 0.23.x only supports v13-14).

The load tests run ONLY when the installed core matches the requirements.txt
pin (CORE_PIN).  On CI the pin is installed first, so the tests run for real.
On machines with a stale/different core (e.g. system Python 3.9 which cannot
install core 0.25.x), they skip — the pin mismatch is an environment issue,
not a code defect, and running them there would just report broken grammars
that the pin already fixes.

The install_state() classification logic (missing vs incompatible vs
import-error) is tested independently of the local environment via
monkeypatched failures.

Run from the scripts/ directory:
    python -m pytest source_map_v2/tests/test_ts_smoke.py -q
"""

from __future__ import annotations

import importlib.metadata as _md

import pytest

from source_map_v2.extractors import tshelpers as H

# Must match the ``tree-sitter==`` pin in skills/specback/scripts/requirements.txt.
CORE_PIN = "0.25.1"


def _core_matches_pin() -> bool:
    try:
        return _md.version("tree-sitter") == CORE_PIN
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _core_matches_pin(),
    reason=f"tree-sitter core does not match requirements.txt pin {CORE_PIN}",
)

_ALL_LANGUAGES = sorted(H.TREE_SITTER_BACKED)


@pytest.fixture(autouse=True)
def _clear_install_state_cache():
    """install_state is lru_cached; clear it so monkeypatched _load_language
    failures are actually observed (and so one test's result can't leak into
    the next)."""
    H.install_state.cache_clear()
    yield
    H.install_state.cache_clear()


def test_every_backed_language_loads() -> None:
    broken = [lang for lang in _ALL_LANGUAGES if not H.have(lang)]
    assert broken == [], (
        f"tree-sitter grammars failed to load: {broken}. "
        "Check for grammar/core version mismatches (see requirements.txt pins)."
    )


def test_install_state_is_ok_for_every_language() -> None:
    bad = {
        lang: H.install_state(lang)
        for lang in _ALL_LANGUAGES
        if H.install_state(lang) != H.STATE_OK
    }
    assert bad == {}, f"non-ok grammar install states: {bad}"


def test_install_state_distinguishes_missing_from_broken() -> None:
    # A language with no grammar mapping reports MISSING, not one of the
    # installed-but-broken states.
    assert H.install_state("not-a-real-language") == H.STATE_MISSING


def test_install_state_reports_missing_on_import_error(monkeypatch) -> None:
    # Grammar module cannot be imported -> MISSING (same as "not installed").
    def fake_load(lang: str):
        raise ImportError("No module named 'tree_sitter_whatever'")

    monkeypatch.setattr(H, "_load_language", fake_load)
    assert H.install_state("python") == H.STATE_MISSING


def test_install_state_reports_incompatible_on_version_mismatch(monkeypatch) -> None:
    # Grammar imports fine but Parser() rejects its Language version ->
    # INCOMPATIBLE, so the pipeline warns about the version pin, not "pip install".
    def fake_load(lang: str):
        raise ValueError("Incompatible Language version 15. Must be between 13 and 14")

    monkeypatch.setattr(H, "_load_language", fake_load)
    assert H.install_state("python") == H.STATE_INCOMPATIBLE


def test_install_state_reports_import_error_on_other_failures(monkeypatch) -> None:
    # Grammar installed but crashes for an unrelated reason -> IMPORT_ERROR.
    def fake_load(lang: str):
        raise OSError("dlopen: symbol not found")

    monkeypatch.setattr(H, "_load_language", fake_load)
    assert H.install_state("python") == H.STATE_IMPORT_ERROR
