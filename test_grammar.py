#!/usr/bin/env python
""" Takes in two files names as arguments: the PyMeta grammar file and the
    test file for that syntax. It creates a grammar from the file. For
    each line in the test file, it splits the line by the character sequence
    "|||". The left hand side of that spit is the piece of string to test,
    and the right is the production name from the syntax file to run on that
    string.

    Outputs the result of each test, and reports the failures.
"""
import sys
from pymeta.grammar import OMeta
from pymeta.runtime import ParseError
from optparse import OptionParser

def run_tests(grammar_iter, tests_iter):
    """ Creates an OMeta grammar from the given grammar iterable, and
        tries to parse each test in the given test iterable
    """
    grammar_string = "".join(grammar_iter)
    parser = OMeta.makeGrammar(grammar_string, {})

    results = []
    failures = []
    for test in tests_iter:
        test_string, production = [x.strip() for x in test.split("|||")]

        application = parser(test_string)
        try:
            application.apply(production)
            results.append(".")
        except Exception as e:
            results.append("F")
            fail = "Test %s, %s failed" % (test_string, production)
            ex   = "%s: %s" % (e.__class__.__name__, e)
            failures.append((fail, ex))

    return results, failures

if __name__ == "__main__":
    opt = OptionParser()
    opt.add_option("-i", "--std-in", action="store_true", dest="from_stdin",
            help="Should the grammar file be read from stdin?", default=False)
    options, args = opt.parse_args()

    ac = len(args)
    if (options.from_stdin and ac != 1) or (ac != 2 and not options.from_stdin):
        print "usage: tester.py [-i] [<grammar_file>] <tests_file>"
        sys.exit(-1)

    if options.from_stdin:
        grammar_file = sys.stdin
        tests_file  = open(args[0])
    else:
        grammar_file = open(args[0])
        tests_file  = open(args[1])

    results, failures = run_tests(grammar_file, tests_file)
    print "===Results==="
    print "".join(results)
    if failures:
        print
        print "===Failures==="
        for test, exception in failures:
            print test
            print exception
            print "---"
