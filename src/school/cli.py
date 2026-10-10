
import argparse
import json
from dataclasses import asdict, is_dataclass

from .parser import import_jsonl
from .repository import InMemorySubmissionRepository


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import student submissions from JSONL"
    )

    parser.add_argument(
        "file",
        help="Path to the JSONL file",
    )

    args = parser.parse_args()

    repository = InMemorySubmissionRepository()
    result = import_jsonl(args.file, repository)

    errors = [
        asdict(error) if is_dataclass(error) else error
        for error in result.errors
    ]

    output = {
        "accepted": result.accepted,
        "duplicates": result.duplicates,
        "conflicts": result.conflicts,
        "errors": errors,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
