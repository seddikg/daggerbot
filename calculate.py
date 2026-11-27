import ast
import operator

MAX_LENGTH = 200       
MAX_EXPONENT = 100     
MAX_ABS = 1e100        

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class UnsafeExpression(ValueError):
    """Raised when an expression is invalid or not allowed."""


def _check(value):
    if abs(value) > MAX_ABS:
        raise UnsafeExpression("Result is too large")
    return value


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    # Only plain ints and floats (type() check also rejects bool)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return _check(node.value)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _check(_UNARY_OPS[type(node.op)](_eval_node(node.operand)))

    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
            raise UnsafeExpression("Exponent is too large")
        return _check(_BINARY_OPS[type(node.op)](left, right))

    raise UnsafeExpression("Unsupported element in expression")


def calculate(expr: str):
    """Safely evaluate a math expression. Raises UnsafeExpression on any problem."""
    expr = expr.strip()
    if not expr or len(expr) > MAX_LENGTH:
        raise UnsafeExpression("Empty or too long")
    try:
        tree = ast.parse(expr, mode="eval")
        return _eval_node(tree)
    except UnsafeExpression:
        raise
    except ZeroDivisionError:
        raise UnsafeExpression("Division by zero")
    except (SyntaxError, RecursionError, MemoryError, OverflowError, ArithmeticError):
        raise UnsafeExpression("Invalid expression")


def is_calculable(expr: str) -> bool:
    try:
        calculate(expr)
        return True
    except UnsafeExpression:
        return False