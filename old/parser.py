import json as jsonlib
from itertools import combinations

def parse_msg(json):
    return parse_congratulations(json) \
        or parse_condolences(json) \
        or parse_status(json)

def parse_congratulations(json):
    if "congratulations" not in json: return False
    if len(json) > 1: return False
    win = json["congratulations"]
    return parse_win(win)

def parse_condolences(json):
    if "condolences" not in json: return False
    if len(json) > 1: return False
    loss = json["condolences"]
    return parse_loss(loss)

def parse_status(json):
    key_count = len(json)
    if key_count == 1:
        return parse_location(json)
    elif key_count == 2:
        return (parse_location(json) and parse_actors(json)) \
            or (parse_location(json) and parse_stuff(json)) \
            or (parse_location(json) and parse_threats(json))
    elif key_count == 3:
        pass
    elif key_count == 4:
        pass
    return False


def parse_win(json):
    return (parse_chronicle(json) and parse_hoard(json) and parse_score(json)) \
        or (parse_score(json) and parse_chronicle(json)) \
        or (parse_score(json) and parse_hoard(json)) \
        or parse_score(json)

def parse_score(json):
    if "score" not in json: return False
