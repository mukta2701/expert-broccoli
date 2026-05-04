"""Interactive CLI playground for the mock chatbot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mock_app.mock_chatbot import chat  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive mock chatbot playground.")
    parser.add_argument(
        "--mode",
        choices=["safe", "unsafe"],
        default="safe",
        help="Chatbot behavior mode.",
    )
    args = parser.parse_args()

    print(f"Mock chatbot started in {args.mode.upper()} mode.")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        try:
            user_input = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nStopping.")
            break

        if user_input.lower() in {"exit", "quit"}:
            print("Stopping.")
            break

        response = chat(user_input, mode=args.mode)
        print(f"Category> {response.category}")
        print(f"Bot> {response.text}")


if __name__ == "__main__":
    main()
