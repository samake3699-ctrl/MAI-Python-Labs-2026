import io
import tokenize
from dataclasses import dataclass


@dataclass(frozen=True)
class CodeToken:
    value: str
    kind: str
    line: int


IGNORED_TOKENS = {
    tokenize.COMMENT,
    tokenize.NL,
    tokenize.NEWLINE,
    tokenize.INDENT,
    tokenize.DEDENT,
    tokenize.ENDMARKER,
    tokenize.ENCODING,
}


def extract_code_tokens(code: str) -> list[CodeToken]:
    """Extraire les tokens significatifs d'un code Python."""

    reader = io.StringIO(code).readline
    results = []

    for token in tokenize.generate_tokens(reader):

        if token.type in IGNORED_TOKENS:
            continue

        results.append(
            CodeToken(
                value=token.string,
                kind=tokenize.tok_name[token.type],
                line=token.start[0],
            )
        )

    return results