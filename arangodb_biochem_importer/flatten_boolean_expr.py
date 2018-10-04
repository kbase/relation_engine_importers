"""
Given a nested list of lexemes that have been parsed from a boolean expression, factor everything
out into a list-of-lists of conjunctions (AND combinations).

For example, given an expression like "(a or b and c) and (e or f)"
It is first parsed into [['a', 'or', 'b', 'and', 'c'], 'and', ['e', 'or', 'f']]
Then it is processed by this module into:
    [['a', 'e'], ['a', 'f'], ['b, 'c', 'e'], ['b', 'c', 'f']]

Terms:
    `lexeme` - a single, atomic syntactic token, such as 'and', 'or', or a keyword such as 'BPLAN_RS02065'
    `keyword` - a user-defined word in an expression such as a gene name -- can be any string except and/or
    `expression` - a nested list of lexemes that represents a parsed expression tree
    `conjunction` - a list of keywords that are all joined together with AND operators
    `disjunction` - a list of conjunctions, where each conjunction is joined by an OR operator
    `term` - either a lexeme or a disjunction
"""


def remove_unknowns(disj):
    """
    Filter out all conjunctions in a disjunction that contain 'Unknown' keywords.
    This can be applied to the resulting value from `flatten_expr`
    """
    return [conj for conj in disj if 'Unknown' not in conj]


def flatten_expr(expr):
    """
    Flatten a nested parsed list of lexemes into a list of conjunctions.
    """
    return traverse_lexemes(expr, convert_expr_to_disjunction)


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


def convert_expr_to_disjunction(expr):
    """
    Convert a list of lexemes like ['a', 'and', ['b', 'or', 'c']] into a list of lists, where each sub-list is
    a separate AND conjunction, and all conjunctions are joined together by OR disjunctions.
    eg. ['a', 'or', 'b', 'and', 'c']
      results in [['a'], ['b', 'c']]

    The expression may have sub-parts that have already recursively been converted into
    disjunctions. For example, this function may be given ['a', 'and', [['b'], ['c', 'd']]]. In
    this case, we will combine the sub-expression according to rules found in the `or_combination`
    and `and_combination` functions.
    eg. with an expr like "(a or b) and (c or d)"
        that has been converted to two sub-expressions `[['a'], ['b']]` and `[['c'], ['d']]`
        then they will get combined here into [['a', 'c'], ['a', 'd'], ['b', 'c'], ['b', 'd']]

    """
    # A disjunction is a list of conjunctions
    disj = []  # type: list
    # Modes set by the 'mode' variable are:
    #   or: we last saw an 'or' operator and will concatenate the next term to the top level
    #   and: we last saw an 'and' operator and will append terms to previous conjunctions
    #   op: we last saw a term and are now expecting an operator
    mode = 'or'  # 'or' is concatenation. We want to start off by concatenating the first term.
    for lexeme in expr:
        if mode == 'and':
            conj = and_combination(disj, lexeme)
            # We will next expect an operator
            mode = 'op'
        elif mode == 'or':
            conj = or_combination(disj, lexeme)
            # We will next expect an operator
            mode = 'op'
        elif mode == 'op':
            # Set the mode to the type of operator
            mode = lexeme
    return conj


def or_combination(disjunction, term):
    """
    Join together a disjunction and another term using an OR operator. If the term is a lexeme, we
    simply append it as a new conjunction to the end of the disjunction. If the term is another
    disjunction, then we concatenate both disjunctions together.
    """
    if isinstance(term, list):
        # Combine two sub-expressions with OR (just concatenates)
        disjunction += term
    else:
        # Append an atom to the whole expression (OR case)
        disjunction.append([term])
    return disjunction


def and_combination(disjunction, term):
    """
    Join a disjunction and another term together with an AND operator. If term is a lexeme,
    then we append it to the last conjunction in the disjunction.

    If `term` is itself a disjunction, then we do a pair-wise combination of every
    conjunction in both disjunctions.

    example: "(a or b) and (c or d)"
    with disjunction as [[a], [b]] and term as [[c], [d]]
    the result is [[a, c], [a, d], [b, c], [b, d]]
    """
    if isinstance(term, list):
        # Combine two sub-expressions with AND
        return [conj1 + conj2 for conj1 in disjunction for conj2 in term]
    else:
        # Append an atom to the last expression (AND case)
        disjunction[-1].append(term)
        return disjunction
