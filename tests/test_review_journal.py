"""The human-review record is a plain-text markdown journal (review/human_review.md),
not a CSV form. Reviews happen in conversation; this file is the written record."""

import config


def test_review_file_is_markdown_journal(channel_ws):
    assert config.paths_for(channel_ws["channel"]).review_file.name == "human_review.md"
