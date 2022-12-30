import ast
import argparse


def remove_docstring(node):  # removes docstrings
    if len(node.body) > 0 and isinstance(node.body[0], ast.Expr) and hasattr(node.body[0], 'value') and isinstance(
            node.body[0].value, ast.Str):
        node.body = node.body[1:]
    return node


class CodeTransformer(ast.NodeTransformer):
    names = set()

    def visit_Name(self, node):  # renames the variables
        if isinstance(node.ctx, ast.Store) or node.id in self.names:
            self.names.add(node.id)
            node.id = "v"
        return node

    def visit_FunctionDef(self, node):  # removes annotations and type definitions
        self.generic_visit(node)
        node.returns = None
        if node.args.args:
            for arg in node.args.args:
                arg.annotation = None
        node = remove_docstring(node)
        node.name = "f"
        return node

    def visit_AsyncFunctionDef(self, node):
        self.generic_visit(node)
        node = remove_docstring(node)
        node.name = "f"
        return node

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        node.name = "c"
        node = remove_docstring(node)
        return node

    def visit_AnnAssign(self, node):  # removes annotations
        self.generic_visit(node)
        return None

    def visit_Import(self, node):  # removes "import ..."
        self.generic_visit(node)
        return None

    def visit_ImportFrom(self, node):  # removes "from .. import ..."
        self.generic_visit(node)
        return None


def simplify(path):  # simplifies code
    data = open(path, 'r', encoding='utf-8').readlines()
    text = '\n'.join(data)

    tree = ast.parse(text)
    optimizer = CodeTransformer()
    tree = optimizer.visit(tree)

    return ast.unparse(tree)


def compare(text1, text2):  # calculates Levenshtein distance between 2 texts
    n = len(text1)
    m = len(text2)

    dp = [[0] * (m + 1) for i in range(n + 1)]
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0:
                dp[i][j] = j
            elif j == 0:
                dp[i][j] = i
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1])
                dp[i][j] = min(dp[i][j], dp[i - 1][j - 1] + (text1[i - 1] != text2[j - 1]))

    ln = max(n, m)
    return (ln - dp[n][m]) / ln


parser = argparse.ArgumentParser()

parser.add_argument('input_path', type=str, help='Input dir for codes to compare')
parser.add_argument('output_path', type=str, help='Output dir for results of comparing')

args = parser.parse_args()

with open(args.output_path, 'w') as f:
    data = open(args.input_path, 'r').readlines()
    for pair in data:
        if len(pair.strip()) == 0:
            continue
        path1, path2 = pair.split()

        code1 = simplify(path1)
        code2 = simplify(path2)

        f.write("{:.2f}\n".format(compare(code1, code2)))
