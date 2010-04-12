#!/usr/bin/env python
""" Takes in a base test file as the first argument using the -f flag
    Parses through the base tests, and replaces values preceding with <
    and proceeded with > with all possible named values of that kind.
    The types must be defined before they can be replaced
    
    i.e. running test_generator.py on the following test file:
    
    "prince" ||| stereotype
    "princess" ||| stereotype
    "noble" ||| stereotype
    {"ran into a stereotype" : [<stereotype>]} ||| event
    
    returns:
    
    "prince" ||| stereotype
    "princess" ||| stereotype
    "noble" ||| stereotype
    {"ran into a stereotype" : ["prince"]} ||| event
    {"ran into a stereotype" : ["princess"]} ||| event
    {"ran into a stereotype" : ["noble"]} ||| event
    
"""

from optparse import OptionParser

def generate_tests(tests_iter):
    raw_lines = []
    test_types = dict()
    results = []
    
    # Store lines and generate dict
    for line in tests_iter:
        
        try:
            test, type = [x.strip() for x in line.split("|||")]
        except ValueError:
            raise Exception("Line %s not formatted correctly" % (line))

        
        if type in test_types:
            # if already exists, append to list
            test_types[type].append(test)
        else:
            # otherwise, make list
            test_types[type] = [test]

        raw_lines.append(line)
    
    # Go through raw lines, and replace words in < > with corresponding value
    # from dict
    strings_to_look_for = ['<' + x + '>' for x in test_types.keys()]
    for raw_line in raw_lines:
        found_replacement = False
        
        for string_to_look_for in strings_to_look_for:
            # For every stirng to find
            if raw_line.find(string_to_look_for) != -1:
                    # Found one of the strings
                    found_replacement = True
                    
                    # Type is the text within <>
                    type = string_to_look_for.replace('<','').replace('>','')
                    
                    # For keeping track of strings to replace it with
                    replacements = []
                    
                    # Parse through the list of type
                    for replace_with in test_types[type]:
                        # Replace the <type_name> with the value
                        replacements.append(raw_line.replace(string_to_look_for,replace_with))
                    
                    # Add replacements to results
                    results.extend(replacements)                
        
        if not found_replacement:
            # We didn't find any <>s so just add raw line
            results.append(raw_line)
        
    
    return results

if __name__ == "__main__":
    opt = OptionParser()
    opt.add_option("-f", "--file", type="string", dest="tests_file",
                   help="File to generate tests from")
    options, args = opt.parse_args()
    
    tests = generate_tests(open(options.tests_file))
    
    print "".join(tests)