import unittest
from arangodb_biochem_importer.flatten_boolean_expr import flatten_expr
from arangodb_biochem_importer.parse_gpr import parse_gpr


class TestFlattenBooleanExpression(unittest.TestCase):

    def test_flatten_expr(self):
        expr = '(a and b or c) and (c and d or e and f)'
        parsed = parse_gpr(expr)
        result = flatten_expr(parsed.value)
        expected = [['a', 'b', 'c', 'd'], ['a', 'b', 'e', 'f'], ['c', 'c', 'd'], ['c', 'e', 'f']]
        self.assertEqual(result, expected, expr)
