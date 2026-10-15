import ast


class IdentifierNormalizer(ast.NodeTransformer):
    """Remplacer les identifiants de façon cohérente."""

    def __init__(self):
        self.names = {}

    def normalize(self, name: str) -> str:
        if name not in self.names:
            number = len(self.names) + 1
            self.names[name] = f"name_{number}"

        return self.names[name]

    def visit_Name(self, node: ast.Name):
        node.id = self.normalize(node.id)
        return node

    def visit_arg(self, node: ast.arg):
        node.arg = self.normalize(node.arg)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        node.name = self.normalize(node.name)
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        node.name = self.normalize(node.name)
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        node.name = self.normalize(node.name)
        self.generic_visit(node)
        return node


def extract_ast_features(code: str) -> set[str]:
    """Extraire les représentations des sous-arbres AST."""

    try:
        tree = ast.parse(code)

    except SyntaxError as error:
        raise ValueError(
            f"Code Python invalide à la ligne {error.lineno}: "
            f"{error.msg}"
        ) from error

    if not tree.body:
        return set()

    normalizer = IdentifierNormalizer()
    normalized_tree = normalizer.visit(tree)

    return {
        ast.dump(node, include_attributes=False)
        for node in ast.walk(normalized_tree)
        if isinstance(node, (ast.stmt, ast.expr))
    }


def compare_ast_code(
    code_a: str,
    code_b: str,
) -> float | None:
    """Comparer deux programmes à partir de leurs structures AST."""

    features_a = extract_ast_features(code_a)
    features_b = extract_ast_features(code_b)

    if not features_a or not features_b:
        return None

    intersection = len(features_a & features_b)
    union = len(features_a | features_b)

    return intersection / union