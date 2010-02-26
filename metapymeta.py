#!/usr/bin/env python

ometaGrammar = """
quotedString ::= (('"' | '\''):q (~<exactly q> <anything>)*:xs <exactly q>
                     => ''.join(xs)
rule ::= <bracketexpr>:a <spaces> <token '::='> <spaces> (<bracketexpr> |
name ::= <letterOrDigit>+:ls => ''.join(ls)
bracketexp ::= '<'<name>:e'>' => e
commaexpr ::= (<token ','> <spaces> <bracketexp>:a <spaces>
               | <bracketexp>)
orexpr ::=
lobexpr ::= ( <bracketexpr> |
"""

# quotedString === "frob"
#
# rule === <frob> ::= and the rest
#
# name === frob
#
# bracketexpr === <frob> -> frob
#
# commaexpr === <frob> , <foo> ...
#
# orexpr === | ...
#
# lobexpr ===


Example = OMeta.makeGrammar(ometaGrammar, {})
