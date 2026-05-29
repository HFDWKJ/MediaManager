"""Create sample [Original Name] folders for testing."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create test extraction folders")
    parser.add_argument(
        "--target",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "test_data" / "library",
    )
    args = parser.parse_args()
    base = args.target
    base.mkdir(parents=True, exist_ok=True)

    # Folder 1
    f1 = base / "[Cool Video]"
    (f1 / "clips").mkdir(parents=True, exist_ok=True)
    (f1 / "intro.mp4").write_bytes(b"fake video intro " * 100)
    (f1 / "cover.jpg").write_bytes(b"fake jpeg " * 50)
    (f1 / "clips" / "part1.mp4").write_bytes(b"fake part1 " * 100)

    # Folder 2 — similar name for match testing
    f2 = base / "[Cool Video 2024]"
    f2.mkdir(parents=True, exist_ok=True)
    (f2 / "main.mp4").write_bytes(b"different content " * 100)

    # Folder 3 — exact duplicate name on "different device" path
    f3 = base / "archive" / "[Cool Video]"
    f3.mkdir(parents=True, exist_ok=True)
    (f3 / "intro.mp4").write_bytes(b"fake video intro " * 100)
    (f3 / "cover.jpg").write_bytes(b"fake jpeg " * 50)

    print(f"Test data created at: {base.resolve()}")
    print("Add this folder in the app: Add Library Root -> select the path above")


if __name__ == "__main__":
    main()
