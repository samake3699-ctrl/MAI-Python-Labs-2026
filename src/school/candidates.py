"""Candidats de similarité : filtres, modèles autorisés et preuves vérifiables.

Le score est une indication technique, jamais un jugement de plagiat.
"""
from __future__ import annotations

import tokenize
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from .ast_similarity import compare_ast_code
from .features import CodeToken, extract_code_tokens
from .models import Submission
from .similarity import compare_python_code


@dataclass(frozen=True)
class LineEvidence:
    """Un 3-gramme commun et les lignes réelles des deux codes."""
    left_start: int
    left_end: int
    right_start: int
    right_end: int
    matching_tokens: tuple[str, str, str]


@dataclass(frozen=True)
class SimilarityCandidate:
    """Une comparaison entre deux étudiants du même devoir."""
    source_id: str
    candidate_id: str
    token_score: float | None
    ast_score: float | None
    evidence: LineEvidence | None
    authorized_template_lines_source: tuple[int, ...]
    authorized_template_lines_candidate: tuple[int, ...]
    warning: str | None = None


def without_authorized_template(
    submission: Submission, templates: Mapping[str, str]
) -> tuple[str, tuple[int, ...]]:
    """Masquer les lignes exactes autorisées en conservant leur numérotation."""
    template = templates.get(submission.template_id or "")
    if not template:
        return submission.code, ()

    allowed_lines = {line for line in template.splitlines() if line.strip()}
    masked_lines: list[str] = []
    removed: list[int] = []
    for number, line in enumerate(submission.code.splitlines(), start=1):
        if line in allowed_lines:
            masked_lines.append("")  # Conserve la position des autres lignes.
            removed.append(number)
        else:
            masked_lines.append(line)
    return "\n".join(masked_lines) + "\n", tuple(removed)


def common_token_evidence(left: str, right: str) -> LineEvidence | None:
    """Trouver un 3-gramme commun, avec lignes réelles dans chaque code."""
    a: list[CodeToken] = extract_code_tokens(left)
    b: list[CodeToken] = extract_code_tokens(right)
    right_windows: dict[tuple[str, str, str], tuple[int, int]] = {}
    for i in range(len(b) - 2):
        key = (b[i].value, b[i + 1].value, b[i + 2].value)
        right_windows.setdefault(key, (b[i].line, b[i + 2].line))
    for i in range(len(a) - 2):
        key = (a[i].value, a[i + 1].value, a[i + 2].value)
        if key in right_windows:
            r_start, r_end = right_windows[key]
            return LineEvidence(a[i].line, a[i + 2].line, r_start, r_end, key)
    return None


def iter_candidates(
    source: Submission,
    submissions: Iterable[Submission],
    templates: Mapping[str, str],
) -> Iterable[SimilarityCandidate]:
    """Comparer paresseusement une soumission aux travaux éligibles.

    On garde les versions distinctes de chaque autre étudiant ; on exclut
    le même étudiant, la même soumission et les autres exercices.
    """
    source_code, source_masked = without_authorized_template(source, templates)
    for other in submissions:
        if other.submission_id == source.submission_id:
            continue
        if other.assignment_id != source.assignment_id:
            continue
        if other.student_id == source.student_id:
            continue

        other_code, other_masked = without_authorized_template(other, templates)
        token_score: float | None = None
        ast_score: float | None = None
        evidence: LineEvidence | None = None
        warnings: list[str] = []

        try:
            token_score = compare_python_code(source_code, other_code)
            evidence = common_token_evidence(source_code, other_code)
        except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
            warnings.append(f"Tokenisation impossible : {exc}")

        try:
            ast_score = compare_ast_code(source_code, other_code)
        except ValueError as exc:
            warnings.append(f"AST impossible : {exc}")

        yield SimilarityCandidate(
            source_id=source.submission_id,
            candidate_id=other.submission_id,
            token_score=token_score,
            ast_score=ast_score,
            evidence=evidence,
            authorized_template_lines_source=source_masked,
            authorized_template_lines_candidate=other_masked,
            warning="; ".join(warnings) or None,
        )


def top_candidates(
    source: Submission,
    submissions: Iterable[Submission],
    templates: Mapping[str, str],
    limit: int = 5,
) -> list[SimilarityCandidate]:
    """Classer les candidats ; tri en mémoire O(N), à profiler au Lab 2."""
    if limit < 0:
        raise ValueError("limit doit être positif ou nul")
    results = list(iter_candidates(source, submissions, templates))
    results.sort(
        key=lambda item: (
            -max((score for score in (item.token_score, item.ast_score)
                  if score is not None), default=-1.0),
            item.candidate_id,
        )
    )
    return results[:limit]
