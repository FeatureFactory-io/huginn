"""UX design-system preview views. Development only."""

from django.shortcuts import render


def palette_preview(request):
    """Render the ESM-03 palette / Dashboard mockup for visual sign-off."""
    return render(request, "ui/ux/palette_preview.html")
