import unittest
from arangodb_biochem_importer.flatten_boolean_expr import combine_operands, and_expressions, flatten_expr
from arangodb_biochem_importer.parse_gpr import parse_gpr


class TestFlattenBooleanExpression(unittest.TestCase):

    def test_combine_operands(self):
        examples = {
            'a': [['a']],
            'a or b': [['a'], ['b']],
            'a and b': [['a', 'b']],
            'a or b and c': [['a'], ['b', 'c']],
            'a and b or c': [['a', 'b'], ['c']],
            'a or b and c and d or f and g or e': [['a'], ['b', 'c', 'd'], ['f', 'g'], ['e']]
        }
        for (expr, expected) in examples.items():
            parsed = parse_gpr(expr)
            result = combine_operands(parsed.value)
            self.assertEqual(result, expected, expr)

    def test_flatten_expr(self):
        expr = '(a and b or c) and (c and d or e and f)'
        parsed = parse_gpr(expr)
        result = flatten_expr(parsed.value)
        expected = [['a', 'b', 'c', 'd'], ['a', 'b', 'e', 'f'], ['c', 'c', 'd'], ['c', 'e', 'f']]
        self.assertEqual(result, expected, expr)
