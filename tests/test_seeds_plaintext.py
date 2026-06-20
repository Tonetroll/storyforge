"""The seed queue is a PLAIN-TEXT file (seeds/seeds.txt): you write one idea per
line in plain words and that is what's fed to the pipeline -- no JSON required."""

import config
from pipeline import chain


def test_seeds_path_is_plain_text_file(channel_ws):
    assert config.paths_for(channel_ws["channel"]).seeds.name == "seeds.txt"


def test_run_channel_reads_plain_text_ideas_verbatim(channel_ws, monkeypatch):
    paths = channel_ws["paths"]
    fed = []
    monkeypatch.setattr(chain, "run_chain",
                        lambda brief, **kw: fed.append(brief) or {"brief": brief})
    paths.seeds.write_text(
        "# a comment line is skipped\n"
        "Messi and Ronaldo and the GOAT pressure.\n"
        "A lighthouse keeper's last night before the light goes automated.\n",
        encoding="utf-8",
    )
    chain.run_channel(channel=channel_ws["channel"])
    assert fed == [
        "Messi and Ronaldo and the GOAT pressure.",
        "A lighthouse keeper's last night before the light goes automated.",
    ]
