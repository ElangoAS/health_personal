from __future__ import annotations

import json

from .pipeline import run_pipeline


def main() -> None:
    """Run the full Strava ingestion and analytics pipeline."""
    summary = run_pipeline()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
