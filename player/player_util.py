''' The player module contains the classes necessary to correctly traverse the
    dungeon.
'''
import logging

__all__ = ['Location', 'Items', 'Threats', 'Player']


class WinMessage(object):
    ''' Represents a win message '''

    def __init__(self, message):
        self._message = message
        self._score = message['score']

        self._hoard, self._chronicle = False, False
        if 'hoard' in message:
            self._hoard = message['hoard']

        if 'chronicle' in message:
            self._chronicle = message['chronicle']

    def __str__(self):
        return str(self.message)

    @property
    def message(self):
        return self._message

    @property
    def score(self):
        return self._score

    @property
    def hoard(self):
        return self._hoard

    @property
    def chronicle(self):
        return self._chronicle


class LossMessage(object):

    def __init__(self, message):
        self._error, self._win = False, False

        if "error" in message:
            self._error = message['error']
        else:
            self._win = WinMessage(message)

    @property
    def error(self):
        return self._error

    @property
    def win(self):
        return self._win


class Location(object):
    ''' Represents a location inside the dungeon. This is the base class
        for all types of locations. Its main use us to use the constructor
        from_json, which takes in location JSON and calls the proper
        constructor.

        >>> outside1 = Location.from_json('outside the castle')
        >>> outside2 = Location.from_json('outside the castle')
        >>> outside1 == outside2
        True
        >>> outside1.is_outside
        True
        >>> outside1.exits == set([])
        True

        >>> moat = Location.from_json('in the moat')
        >>> moat.is_outside
        False
        >>> moat.in_moat
        True
        >>> moat == outside1
        False

        >>> json1 = {'room' : { 'purpose' : 'Foo',
        ...                     'attributes' : ['bar', 'baz'],
        ...                     'exits' : ['north', 'south'] }}
        >>> json2 = {'room' : { 'purpose' : 'Foo',
        ...                     'attributes' : ['baz', 'bar'],
        ...                     'exits' : ['south', 'north'] }}
        >>> room1 = Location.from_json(json1)
        >>> room2 = Location.from_json(json2)
        >>> room1 == room2
        True
        >>> room1.is_outside
        False
        >>> room1.exits == set(['north', 'south'])
        True
    '''

    @classmethod
    def from_json(cls, location):
        ''' Given some JSON, construct the proper Location from it '''
        if location == "outside the castle":
            return Outside()
        elif location == "in the moat":
            return InMoat()
        elif 'room' in location:
            room = location['room']
            return Room(room)
        else:
            raise Exception('Invalid JSON for Location: %s' % location)

    @property
    def identity(self):
        ''' The unique identifier for this Location '''
        return 'NOT-UNIQUE'

    @property
    def is_outside(self):
        ''' Is the location outside the castle? '''
        return False

    @property
    def in_moat(self):
        ''' Is this location in the moat? '''
        return False

    @property
    def exits(self):
        ''' Return the set of all exits this location has. '''
        return frozenset([])

    def __eq__(self, other):
        return hasattr(other, "identity") and self.identity == other.identity


class Room(Location):
    ''' Represents a Room in the dungeon which has exits. Each room is uniquely
        identified by its purpose and attributes.
    '''

    def __init__(self, room):
        self._identity = frozenset([room['purpose']] + room['attributes'])
        self._exits = frozenset(room['exits'])

    @property
    def identity(self):
        return self._identity

    @property
    def exits(self):
        return self._exits


class Outside(Location):
    ''' Represents anywhere outside of the dungeon. Outside is just outside.
        It is not unique, so its identity is not unique.
    '''

    @property
    def identity(self):
        return 'OUTSIDE'

    @property
    def is_outside(self):
        return True


#TODO: Figure out what the moat does
class InMoat(Location):
    ''' Represents being inside the moat. Not sure what the moat does though.
        It is not unique, so its identity is not unique.
    '''

    @property
    def identity(self):
        return "INMOAT"

    @property
    def in_moat(self):
        return True


class Items(object):
    ''' Convience class for items in a room. Sorts items into useful groups.
        The properties return defensive copies of the attribute lists.
    '''

    def __init__(self, items):
        self._has_frog = False
        self._treasures = []
        self._weapons = []
        self._artifacts = []
        for item in items:
            if 'frog' in item:
                self._has_frog = True
            elif 'treasure' in item:
                self._treasures.append((item['treasure'], item['value']))
            elif 'weapon' in item:
                self._weapons.append((item['weapon'], item['lethality']))
            else: # artifact
                self._artifacts.append((item['artifact'],
                                        tuple(item['description'])))

    @property
    def has_frog(self):
        return self._has_frog

    @property
    def treasures(self):
        return [] + self._treasures

    @property
    def weapons(self):
        return [] + self._weapons

    @property
    def artifacts(self):
        return [] + self._artifacts


class Threats(object):
    ''' Convience class for threats'''

    def __init__(self, problems):

        self._attacked = False
        # Assign null values to indicate we haven't received anything
        self._ill, self._tired, self._injured, self._attacked_by = \
            None, None, None, None

        for problem in problems:
            if 'ill' in problem:
                self._ill = problem['ill']

            if 'tired' in problem:
                self._tired = problem['tired']

            if 'injured' in problem:
                self._injured = problem['injured']

            if 'attacked' in problem:
                self._attacked = True
                self._attacked_by = problem['attacked']

    @property
    def ill(self):
        return self._ill

    @property
    def health(self):
        return self._injured

    @property
    def tired(self):
        return self._tired

    @property
    def attacked(self):
        return self._attacked

    @property
    def attacked_by(self):
        return self._attacked_by


class Player(object):
    ''' Abstract class to represent any game player. It has attributes for
        tracking inventory.Its handle_response is passed JSON, and that JSON is
        converted into the proper objects. These objects are passed to the
        next_move method, whose implementation is left up to the implementing
        class. After the implementing class decides on a move, the last room
        seen and changes in health are recorded.
    '''

    def __init__(self):
        self.prev_health, self.prev_tired, self.prev_ill = 9, 9, 9 # Statuses
        self.weapons, self.artifacts, self.treasure = [], [], []   # Inventory
        self.last_visited_location = None   # The location we saw last

    def handle_response(self, json):
        ''' Converts the given json into useable objects. Returns either a
            string, which is sent to the dungeon program, or False to indicate
            to stop playing
        '''

        if 'congratulations' in json:
            win = WinMessage(json['congratulations'])
            logging.info('You won. Score:' + str(win.score) + \
                         ' Hoard: ' + str(win.hoard) + \
                         ' Chronicle: ' + str(win.chronicle))
            return False

        if 'condolences' in json:
            loss = LossMessage(json['condolences'])
            logging.info('You lost. Error: ' + str(loss.error) + \
                         '\n Win: ' + str(loss.win))
            return False

        location = Location.from_json(json['location'])
        items, threats = Items([]), Threats([])
        if 'stuff' in json:
            items = Items(json['stuff'])

        if 'threats' in json:
            threats = Threats(json['threats'])

            logging.info('THREATS. HEALTH: ' + str(threats.health))
            logging.info('THREATS. TIRED: ' + str(threats.tired))
            logging.info('THREATS. ATTACKED: ' + str(threats.attacked))
            logging.info('THREATS. ATTACKED BY: ' + str(threats.attacked_by))

        move = self.next_move(location, items, threats)
        self.last_visited_location = location.identity

        # 'or' statement because we should use previous if
        # there's not an update
        self.prev_health = threats.health or self.prev_health
        self.prev_tired = threats.tired or self.prev_tired
        self.prev_ill = threats.ill or self.prev_ill

        return move

    def next_move(self, location, items, threats):
        ''' Determines the player's next move in the dungeon '''
        raise NotImplementedError

    # Helper functions for signaling to carry or drop items in the room
    def carry_frog(self):
        return Player.make_message("carry", "frog", "")
    def carry_weapon(self, weapon):
        return self.carry_message("weapon", self.weapons, weapon)
    def carry_treasure(self, treasure):
        return self.carry_message("treasure", self.treasure, treasure)
    def carry_artifact(self, artifact):
        return self.carry_message("artifact", self.artifacts, artifact)
    def drop_weapon(self, weapon):
        return self.drop_message("weapon", self.weapons, weapon)
    def drop_treasure(self, treasure):
        return self.drop_message("treasure", self.treasure, treasure)
    def drop_artifact(self, artifact):
        return self.drop_message("artifact", self.artifacts, artifact)

    def carry_message(self, item_type, inventory_list, item):
        ''' Add an item to one of our inventories when we carry it '''
        inventory_list.append(item)
        return self.make_message("carry", item_type, item)

    def drop_message(self, item_type, inventory_list, item):
        ''' Remove an item to one of our inventories when we drop it '''
        inventory_list.remove(item)
        return self.make_message("drop", item_type, item)

    @classmethod
    def make_message(cls, action, item_type, item):
        ''' Returns a message for carrying an object '''

        if item_type == "frog":
            return "(%s (frog))" % action

        name, etc = item
        if item_type == "artifact":
            etc = " ".join(map(lambda x: '"%s"' % x, etc))

        return "(%s (%s \"%s\" %s))" % (action, item_type, name, etc)


if __name__ == '__main__':
    # When run as a python file, take all the docstrings and run them as tests
    import doctest
    doctest.testmod()
