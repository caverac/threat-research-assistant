"""CLI entry point for docs building."""


def main() -> None:
    """Build documentation."""
    import subprocess
    import sys

    sys.exit(subprocess.call(["mkdocs", "build"]))  # noqa: S603, S607
