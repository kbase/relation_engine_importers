"""
Parse a boolean equations such as "(a or b and c) and (d or a and b) and c or z"
The above is translated into a simple list of strings:
    [['a', 'or', 'b', 'and', 'c'], 'and', ['d', 'or', 'a', 'and', 'b'], 'and', 'c', 'or', 'z']
"""
import parsec as p


def parse_gpr(string):
    """Parse a gene boolean expression."""
    return program(string, 0)


# Stuff to discard
whitespace = p.regex(r'\s+')
ignore = p.many(whitespace)


# A token with all ignore chars ignored
def lexeme(parser):
    return parser.skip(ignore)


# All our basic tokens
lparen = lexeme(p.string('('))
rparen = lexeme(p.string(')'))
symbol = lexeme(p.regex(r'[\d\w_\-\.]+'))
op = lexeme(p.regex(r'(and|or)'))


@p.generate('compound expression')
def compound_expr():
    """An expression with multiple terms, and optionally with surrounding parens."""
    yield lparen
    es = yield p.many(expr)
    yield rparen
    return es


# Atoms get parsed into plain strings
atom = op | symbol
# Expressions get parsed into lists of atoms (strings)
expr = atom | compound_expr
program = p.many(expr).skip(ignore)
