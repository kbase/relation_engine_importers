"""
Given a nested list of lexemes that have been parsed from a boolean expression, factor everything
out into a list-of-lists of conjunctions (AND combinations).

For example, given an expression like "(a or b and c) and (e or f)"
It is first parsed into [['a', 'or', 'b', 'and', 'c'], 'and', ['e', 'or', 'f']]
Then it is processed by this module into:
    [['a', 'e'], ['a', 'f'], ['b, 'c', 'e'], ['b', 'c', 'f']]
"""


def flatten_expr(expr):
    """
    Flatten a nested parsed list of lexemes into a list of conjunctions.
    """
    return traverse_lexemes(expr, combine_operands)


def traverse_lexemes(expr, fn):
    """
    Apply a function to every expression in a lexeme tree, bottom-up.
    Eg. given [['a', 'and', 'b'], 'or', ['c', 'and', 'd']]
    It applies the function like: fn([fn(['a', 'and', 'b']), 'or', fn(['c', 'and', 'd'])])

    This is recursive. We're not worried about stack overflow here.
    """
    if isinstance(expr, str):
        return expr  # base case
    return fn([traverse_lexemes(term, fn) for term in expr])


def combine_operands(expr):
    """
    Convert a list of lexemes like ['a', 'and', 'b'] into a list of lists, where each sub-list is
    a separate AND conjunction.
    eg. ['a', 'or', 'b', 'and', 'c']
      results in [['a'], ['b', 'c']]

    If there are sub-expressions that have previously been combined, then they will get combined
    using `and_expressions` (or in the case of an `or`, just concatenating the two sub-expressions)
    eg. with an expr like "(a or b) and (c or d)"
        that has been converted to two sub-expressions `[['a'], ['b']]` and `[['c'], ['d']]`
        then they will get combined here into [['a', 'c'], ['a', 'd'], ['b', 'c'], ['b', 'd']]

    Modes are:
      or: we last saw an 'or' operator and will concatenate the next term to the top level
      and: we last saw an 'and' operator and will append terms to previous conjunctions
      op: we last saw a term and are now expecting an operator
    """
    # A list of conjunctions
    conj = []  # type: list
    mode = 'or'  # 'or' is concatenation. We want to start off by concatenating the first term.
    for lexeme in expr:
        if mode == 'and':
            if isinstance(lexeme, list):
                # Combine two sub-expressions with AND
                conj = and_expressions(conj, lexeme)
            else:
                # Append an atom to the last expression (AND case)
                conj[-1].append(lexeme)
            # We will next expect an operator
            mode = 'op'
        elif mode == 'or':
            if isinstance(lexeme, list):
                # Combine two sub-expressions with OR (just concatenates)
                conj += lexeme
            else:
                # Append an atom to the whole expression (OR case)
                conj.append([lexeme])
            # We will next expect an operator
            mode = 'op'
        elif mode == 'op':
            # Set the mode to the type of operator
            mode = lexeme
    return conj


def and_expressions(expr1, expr2):
    """
    Join two expressions together with an 'and' conjunction. This does a pairwise combination of
    every conjunction.

    example: "(a or b) and (c or d)"
    with expr1 as [[a], [b]] and expr2 as [[c], [d]]
    result is [[a, c], [a, d], [b, c], [b, d]]
    """
    return [conj1 + conj2 for conj1 in expr1 for conj2 in expr2]
