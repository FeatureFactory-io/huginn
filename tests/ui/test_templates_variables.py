"""S5 Checkpoint: UI Templates — verify mockup coverage."""

from pathlib import Path


def test_variables_mockup_exists():
    """Variables tab mockup exists."""
    template_path = Path("ui/templates/ui/mockups/variables/view.html")
    assert template_path.exists(), f"Variables mockup missing: {template_path}"


def test_projects_view_mockup_exists():
    """Projects view mockup with informer bar exists."""
    template_path = Path("ui/templates/ui/mockups/projects/view.html")
    assert template_path.exists(), f"Projects view mockup missing: {template_path}"


def test_sitrep_list_mockup_exists():
    """SitRep list mockup with Variables column exists."""
    template_path = Path("ui/templates/ui/mockups/sitrep/list.html")
    assert template_path.exists(), f"SitRep list mockup missing: {template_path}"


def test_sitrep_view_mockup_exists():
    """SitRep view mockup with variables snapshot exists."""
    template_path = Path("ui/templates/ui/mockups/sitrep/view.html")
    assert template_path.exists(), f"SitRep view mockup missing: {template_path}"
