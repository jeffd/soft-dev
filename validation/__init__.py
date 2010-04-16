''' Module which handles the validation for our project.
    This file defines a method which takes in a string of
    a response from the game program, and will check it against
    the grammar file saved in this directory
'''
from os import path

from pymeta.grammar import OMeta
from pymeta.runtime import ParseError

from translate import convert_lines

__all__ = ['validate']

# The file which will contain the bnf grammar for the game responses
BNF_FILE = path.join(path.dirname(path.abspath(__file__)), "./bnf_10.txt")
# The file which contains some base grammar definitions for JSON
JSON_GRAMMAR_FILE = path.join(path.dirname(path.abspath(__file__)), "./json_base.grm")

# The name of the production which all messages extend from in the grammar
TOP_PRODUCTION = "msg"

# Convert the BNF into pymeta, then add the JSON base to it
_grammar = "\n\n".join(convert_lines(open(BNF_FILE)))
_grammar += "\n\n" + "".join(open(JSON_GRAMMAR_FILE))

# Make the parser from it
_parser  = OMeta.makeGrammar(_grammar, {})

def validate(response, production=TOP_PRODUCTION):
    ''' Trys to validate the given response with the loaded grammar.
        Returns true if the response is valid in the grammar
    '''
    application = _parser(response)
    application.apply(production)
    return True
