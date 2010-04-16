"""
    Takes a file containing a CFG with lines similar to:
        <state1> ::= { "blah" : <state2> }
        <state2> ::= []
                  |  [1]
    and converts it to PyMeta syntax
"""
from re import compile

production_start = compile("\s*<(.*?)>\s*::=\s*(.*)")
production_cont  = compile("\s*\|\s*(.*)")
production_ref   = compile("<.*?>")

def convert_lines(lines):
    new_prod = None
    prod_body = []
    for line in lines:
        match = production_start.match(line)
        if match:
            if new_prod:
                body = sorted(prod_body, lambda x, y: len(y) - len(x))
                prod = ["%s ::= %s" % (new_prod, body.pop(0))]
                for body_line in body:
                    prod.append("        | %s" % body_line)
                yield "\n".join(prod)
                new_prod = None
                prod_body = []
            new_prod, line = match.groups()
            prod_body.append(convert_body(line))
        match = production_cont.match(line)
        if match:
            line = match.groups()[0]
            prod_body.append(convert_body(line))

    body = sorted(prod_body, lambda x, y: len(y) - len(x))
    prod = ["%s ::= %s" % (new_prod, body.pop(0))]
    for body_line in body:
        prod.append("        | %s" % body_line)
    yield "\n".join(prod)

def convert_body(body):
    result = []
    refs = production_ref.findall(body)
    needs_tokens = production_ref.split(body)
    while needs_tokens:
        tokenize_me = needs_tokens.pop(0)
        tokenized = tokenize(tokenize_me)
        result.extend(tokenized)
        if refs:
            next_ref = refs.pop(0)
            result.append("<spaces>")
            result.append(next_ref)
    return " ".join(result)

def tokenize(str):
    pieces = str.split()
    return ["<token '%s'>" % p for p in pieces]
