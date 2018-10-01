"""
Parse a boolean equation of genes such as:
(L0282 and L0283 and (L37667 or L0269) and Unknown and (L0312 or L0311 or L0281) and L102491 and L0307 and L182797 and (L0302 or L0300 or L0301) and L108430 and Unknown and L0280 and L108989 and L0290 and L0298 and L0274 and L0279 and L0287 and L0275 and L0292 and L102317 and L0304 and L0291)

This describes a required set of active genes for a reaction to occur in a cell.

These expressions get split into an array of arrays, where each child array is a discrete AND
conjuction of terms. We expand out all the OR operators into separate conjunctions.

If any term in a conjunction is an "Unknown", then we discard that whole conjunction.

For example:

    a and (b or c) -> [[a, b], [a, c]]
    Unknown or (a and b) -> [[a, b]]
    a and Unknown and b and c -> []
    a or b or c -> [[a], [b], [c]]
"""
import parsec as p
import sys


whitespace = p.regex(r'\s+')
ignore = p.many(whitespace)


def lexeme(parser):
    return parser.skip(ignore)


lparen = lexeme(p.string('('))
rparen = lexeme(p.string(')'))
symbol = lexeme(p.regex(r'[\d\w_-]+'))
and_op = lexeme(p.string('and'))
or_op = lexeme(p.string('or'))
op = and_op | or_op

atom = op | symbol


@p.generate('binary expression')
def binary_expr():
    yield lparen
    es = yield p.many(expr)
    yield rparen
    return es


expr = atom | binary_expr


def parse_gpr(string):
    """
    Parse a gene boolean expression
    """
    return program(string, 0)


if __name__ == '__main__':
    inp = sys.argv[1]
    program = p.many(expr).skip(ignore)
    print(parse_gpr(inp))
