"""C4: channel name must be validated so paths_for() cannot escape channels/.

The run-time commands (generate/manual/chain/route/learn) call config.paths_for
directly and never pass through channel_setup's lighter check. A channel name
like "../escape" used to resolve OUTSIDE channels/. These tests pin that
paths_for now refuses path traversal, separators, and absolute paths, while
still allowing the falsy default ("_sandbox"), the literal "_sandbox", and
ordinary hyphen/underscore names.
"""

import pytest

import config


# ---------------------------------------------------------------------------
# REJECT: traversal, separators, absolute paths
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "bad",
    [
        "../escape",       # parent-dir traversal via forward slash
        "a/b",             # forward-slash separator
        "..\\x",           # parent-dir traversal via backslash
        "sub\\dir",        # backslash separator
        "..",              # bare parent-dir component
        "C:/Windows",      # absolute path (Windows drive)
        "/etc",            # absolute path (POSIX root)
    ],
)
def test_paths_for_rejects_traversal(bad):
    """Any separator, '..' component, or absolute path raises ValueError, and
    the message names the offending channel so the operator knows what to fix."""
    with pytest.raises(ValueError) as exc:
        config.paths_for(bad)
    assert bad in str(exc.value), (
        f"ValueError for {bad!r} should name the bad channel; got {exc.value!r}"
    )


# ---------------------------------------------------------------------------
# ALLOW: falsy default, literal _sandbox, ordinary names
# ---------------------------------------------------------------------------
def test_paths_for_allows_ordinary_name(monkeypatch, tmp_path):
    """An ordinary hyphenated name resolves to a ChannelPaths whose root sits
    UNDER CHANNELS_DIR (containment holds against the monkeypatched dir)."""
    channels_dir = tmp_path / "channels"
    channels_dir.mkdir()
    monkeypatch.setattr(config, "CHANNELS_DIR", channels_dir)

    P = config.paths_for("football-world-wars")
    assert isinstance(P, config.ChannelPaths)
    assert P.root.resolve() == (channels_dir / "football-world-wars").resolve()
    # Containment: root is strictly inside CHANNELS_DIR.
    assert channels_dir.resolve() in P.root.resolve().parents


def test_paths_for_allows_underscore_and_digits(monkeypatch, tmp_path):
    """Leading underscore and digits are fine (only traversal is rejected)."""
    channels_dir = tmp_path / "channels"
    channels_dir.mkdir()
    monkeypatch.setattr(config, "CHANNELS_DIR", channels_dir)

    for name in ("demo-sports", "demo_sports2", "_sandbox"):
        P = config.paths_for(name)
        assert P.root.resolve() == (channels_dir / name).resolve()


def test_paths_for_none_uses_sandbox(monkeypatch, tmp_path):
    """A falsy channel (None) falls back to the '_sandbox' default under CHANNELS_DIR."""
    channels_dir = tmp_path / "channels"
    channels_dir.mkdir()
    monkeypatch.setattr(config, "CHANNELS_DIR", channels_dir)

    P = config.paths_for(None)
    assert P.root.resolve() == (channels_dir / "_sandbox").resolve()


def test_paths_for_empty_string_uses_sandbox(monkeypatch, tmp_path):
    """An empty string is falsy and must also fall back to '_sandbox', not raise."""
    channels_dir = tmp_path / "channels"
    channels_dir.mkdir()
    monkeypatch.setattr(config, "CHANNELS_DIR", channels_dir)

    P = config.paths_for("")
    assert P.root.resolve() == (channels_dir / "_sandbox").resolve()


def test_paths_for_reads_channels_dir_dynamically(monkeypatch, tmp_path):
    """CHANNELS_DIR is read at call time (tests monkeypatch it), not captured at
    import. A new monkeypatched dir on a later call must take effect."""
    first = tmp_path / "first"
    first.mkdir()
    monkeypatch.setattr(config, "CHANNELS_DIR", first)
    assert config.paths_for("ch").root.resolve() == (first / "ch").resolve()

    second = tmp_path / "second"
    second.mkdir()
    monkeypatch.setattr(config, "CHANNELS_DIR", second)
    assert config.paths_for("ch").root.resolve() == (second / "ch").resolve()
