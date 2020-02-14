import unittest
from modelseed.utils.flatten_boolean_expr import flatten_expr
from modelseed.utils.parse_gpr import parse_gpr


class TestFlattenBooleanExpression(unittest.TestCase):

    def test_flatten_expr(self):
        expr = '(a.a and b or c) and (c and d or e and f)'
        parsed = parse_gpr(expr)
        result = flatten_expr(parsed.value)
        expected = [['a.a', 'b', 'c', 'd'], ['a.a', 'b', 'e', 'f'], ['c', 'c', 'd'], ['c', 'e', 'f']]
        self.assertEqual(result, expected, expr)
