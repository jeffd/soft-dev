from pyparsing import Combine, Optional, Word, Literal, alphas, nums, ParseException, Suppress, delimitedList

# taken from JSONParser_example.py
# FIXME: only accept ints?
number = Combine( Optional('-') + ( '0' | Word('123456789',nums) ) +
                    Optional( '.' + Word(nums) ) +
                    Optional( Word('eE',exact=1) + Word(nums+'+-',nums) ) )

def json_wrapper(expr):
    return Suppress("{") + expr + Suppress("}")

def json_key_value(key, value):
    return key + Suppress(":") + value

def json_key_value_wrapped(key, value):
    return json_wrapper(json_key_value(key,value))

def lw(literal_name, same = True):
    """ Returns a literal with double quotes wrapping it, and results name set to the same literal name """
    literal = Literal('"' + literal_name + '"')
    if same == True:
        return literal.setResultsName(literal_name)
    elif same == False:
        return literal
    else:
        return literal.setResultsName(literal_name)

def string(name):
    return Suppress('"') + Word(alphas + ' ').setResultsName(name) + Suppress('"')

def list_of_strings(name):
    return Suppress("[") + ( string('test') | delimitedList(lw('hello') | lw('world')) ) + Suppress("]")


item_frog = json_key_value_wrapped(lw("frog"), Suppress("[ ]"))
item_treasure = json_wrapper(json_key_value(lw("treasure"),string("treasure_name")) + Suppress(",") + json_key_value(Literal('"value"'), number.setResultsName("treasure_val")))
item_weapon = json_wrapper(json_key_value(lw("weapon"),string("weapon_name")) + Suppress(",") + json_key_value(Literal('"lethality"'), number.setResultsName("lethality_val")))
item_artifact = json_wrapper(json_key_value(lw("artifact"),string("artifact_name")) + Suppress(",") + json_key_value(lw("description"), list_of_strings("description_words")))
item_rule =  item_frog | item_treasure | item_weapon | item_artifact


score_rule = json_key_value(lw("score"), number.setResultsName("score_val"))
hoard_rule = json_key_value(lw("hoard"), Suppress("[") + Optional(delimitedList(item_rule)).setResultsName('items') + Suppress("]"))

win_rule = Suppress("{") + score_rule + Suppress("}") \
           | Suppress("{") + score_rule + Suppress(",") + hoard_rule + Suppress("}") \
           | Suppress("{") + hoard_rule + Suppress(",") + score_rule + Suppress("}")
           
congratulations_rule = json_key_value_wrapped(lw("congratulations"), lw("yay") | win_rule)

strings_to_try = ['{ "congratulations" : "yay" }',
                  '{ "congratulations" : { "score" : 30 } }',
                  '{ "congratulations" : { "hoard" : [ ], "score" : 30 } }',
                  '{ "congratulations" : { "hoard" : [{ "frog" : [ ] }], "score" : 30 } }',
                  '{ "congratulations" : { "hoard" : [{ "frog" : [ ] }, { "treasure" : "gold", "value" : 90 }], "score" : 30 } }',
                  '{ "congratulations" : { "hoard" : [{ "treasure" : "silver plate", "value" : 85 }, { "frog" : [ ] }], "score" : 30 } }',
                  '{ "congratulations" : { "hoard" : [{ "weapon" : "laser gun", "lethality" : 55 }, { "frog" : [ ] }], "score" : 30 } }',
                  '{ "congratulations" : { "hoard" : [{ "frog" : [ ] }, { "weapon" : "laser gun", "lethality" : 55 }], "score" : 30 } }',
                  '{ "congratulations" : { "hoard" : [{ "frog" : [ ] }, { "artifact" : "tomb", "description" : ["hello"] }], "score" : 30 } }',
                  '{ "congratulations" : { "hoard" : [{ "frog" : [ ] }, { "artifact" : "tomb", "description" : ["hello","world"] }], "score" : 30 } }',
                  ]

for string in strings_to_try:
    try:
        result = congratulations_rule.parseString(string)
    except ParseException as p:
        print 'PARSING ERROR on', string, p
        continue
    print 'parsed ', string
    print result.asDict()
    print '------'
