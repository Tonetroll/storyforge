"""Trivial sanity test: the harness imports config and paths_for resolves,
and the isolated channel workspace fixture really points under tmp."""

import config


def test_config_imports_and_paths_for_works():
    paths = config.paths_for("some-channel")
    assert paths.root.name == "some-channel"
    assert paths.candidates.name == "candidates"
    # paths_for(None) -> the shared _sandbox workspace (the legitimate "no channel" case)
    sandbox = config.paths_for(None)
    assert sandbox.root.name == "_sandbox"


def test_channel_ws_fixture_is_isolated(channel_ws, tmp_path):
    paths = channel_ws["paths"]
    assert str(paths.root).startswith(str(tmp_path))
    assert channel_ws["root"].joinpath("profile.md").exists()
