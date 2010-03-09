#!/usr/bin/env python
"""
    Takes a file containing a CFG with lines similar to:
        <state1> ::= { "blah" : <state2> }
        <state2> ::= []
                  |  [1]
    and converts it to PyMeta syntax
"""
import sys
from re import compile
from os import path

production_start = compile("\s*<(.*?)>\s*::=\s*(.*)")
production_cont  = compile("\s*\|\s*(.*)")
production_ref   = compile("<.*?>")

def convert_line(line):
    match = production_start.match(line)
    if match:
        name, body = match.groups()
        return "%s ::= %s" % (name, convert_body(body))
    match = production_cont.match(line)
    if match:
        body = match.groups()[0]
        return "        | %s" % convert_body(body)
    return ""

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

def main(args):
    " Runs the show "
    if len(args) != 2:
        print "usage: %s <cfg-file>" % args[0]
        sys.exit(-1)

    cfg_file = args[1]
    if not path.exists(cfg_file):
        print "file %s not found" % cfg_file
        sys.exit(-1)

    for line in open(cfg_file):
        print convert_line(line.rstrip())

if __name__ == "__main__":
    main(sys.argv)
