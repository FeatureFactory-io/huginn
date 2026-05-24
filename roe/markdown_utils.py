"""Workflow markdown rendering for Rules of Engagement UI."""

from __future__ import annotations

import markdown


def workflow_md_to_html(md_source: str) -> str:
    """Render trusted RoE Workflow markdown to HTML for previews and read-only panels."""
    return markdown.markdown(
        md_source or "",
        extensions=[
            "markdown.extensions.extra",
            "markdown.extensions.sane_lists",
        ],
        output_format="html",
    )
