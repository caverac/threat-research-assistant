"""CLI entry point for generating synthetic threat data."""

from pathlib import Path

from ingestion.synthetic import generate_all


def main() -> None:
    """Generate synthetic OT threat intelligence data."""
    generate_all(Path("data"))
    print("Synthetic data generated successfully.")  # noqa: T201


if __name__ == "__main__":
    main()
