
import json
from pathlib import Path
from typing import Iterable, Iterator, Protocol, TextIO


class TemplateSource(Protocol):
    def get_templates(self) -> dict[str, str]:
        ...


class InMemoryTemplateSource:
    def __init__(self, templates: dict[str, str]) -> None:
        self._templates = dict(templates)

    def get_templates(self) -> dict[str, str]:
        return dict(self._templates)


class JSONLTemplateSource:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._file: TextIO | None = None

    def __enter__(self) -> "JSONLTemplateSource":
        self._file = self.path.open("r", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None

    def get_templates(self) -> dict[str, str]:
        if self._file is None:
            raise RuntimeError(
                "JSONLTemplateSource must be used "
                "inside a with statement"
            )

        self._file.seek(0)
        templates: dict[str, str] = {}

        for line_number, line in enumerate(self._file, start=1):
            if not line.strip():
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON at line {line_number}"
                ) from error

            if not isinstance(data, dict):
                raise ValueError(
                    f"Expected object at line {line_number}"
                )

            template_id = data.get("template_id")
            content = data.get("content")

            if not isinstance(template_id, str):
                raise ValueError(
                    f"Invalid template_id at line {line_number}"
                )

            if not isinstance(content, str):
                raise ValueError(
                    f"Invalid content at line {line_number}"
                )

            if template_id in templates:
                raise ValueError(
                    f"Duplicate template_id: {template_id}"
                )

            templates[template_id] = content

        return templates
