''' The player module contains the classes necessary to correctly traverse the
    dungeon.
'''
import logging

__all__ = ['Location', 'Player', 'BreadcrumbPlayer']

class WinMessage(object):
    ''' Represents a win message '''
    
    def __init__(self, message):
        self._message = message
        self._score = message['score']

        self._hoard, self._chronicle = False
        if 'hoard' in message:
            self._hoard = message['hoard']
        
        if 'chronicle' in message:
            self._chronicle = message['chronicle']
    
    @property
    def score(self):
        return self._score
    
    @property
    def hoard(self):
        return self._hoard
    
    @property
    def chronicle(self):
        return self._chronicle

def LossMessage(object):
    
    def __init__(self, message):
        self._error, self._win = False
        
        if "error" in message:
            self._error = message['error']
        
        if "win" in message:
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
    ''' Convience class for items in a room. Sorts items into useful groups '''

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
                self._artifacts.append(item['artifact'])

    @property
    def has_frog(self):
        return self._has_frog

    @property
    def treasures(self):
        return frozenset(self._treasures)

    @property
    def weapons(self):
        return frozenset(self._weapons)

    @property
    def artifacts(self):
        return frozenset(self._artifacts)


class Player(object):
    ''' Abstract class to represent any game player. It keeps track of the
        number of total moves made. Its handle_response is passed JSON,
        and that JSON is converted into the proper objects. These objects
        are passed to the next_move method, whose implementation is left
        up to the implementing class.
    '''

    def __init__(self):
        self.move_count = -1 # How many moves we have made so far

    def handle_response(self, json):
        ''' Converts the given json into useable objects. Returns either a string,
            which is sent to the dungeon program, or False to indicate to stop
            playing
        '''
        if 'congratulations' in json:
            win = WinMessage(json)
            return False
        
        if 'condolences' in json:
            loss = LossMessage(json)
            return False
        
        location, items, threats = None, None, None
        location = Location.from_json(json['location'])
        if 'stuff' in json:
            items = Items(json['stuff'])
        if 'threats' in json:
            pass

        self.move_count += 1
        return self.next_move(location, items, threats)

    def next_move(self, location, items=None, threats=None):
        ''' Determines the player's next move in the dungeon '''
        raise NotImplementedError


class BreadcrumbPlayer(Player):
    ''' This player keeps track of each room it encounters. Each room has a
        unique description, so this is how rooms are tracked. Once a room is
        entered, a new room is the rooms dict. An exit from this room is chosen
        at random, and once the next room is entered, that exit is marked as
        visited in the previous room.

        A room is truely visited once each of its exits has been explored.
        The player also keeps track of each move necessary to go backwards one
        step in its traveled path.  After encountering such a fully visited
        room, the player pops one move off the traveled path and goes that way.
        It repeats this until it finds a room it can explore more.

        The player also has the ability forget this traveled path, and to also
        flee the maze. When fleeing, the player will only make moves which come
        from the travel path, until no more moves exist on the path. These two
        attributes allow the player to start a path when it finds an exit, and
        then find its way to that exit when it needs to.
    '''

    DIRECTIONS = ['north', 'down', 'east', 'west', 'up', 'south']
    REVERSE_DIRECTIONS = dict(zip(DIRECTIONS, reversed(DIRECTIONS)))

    def __init__(self):
        super(BreadcrumbPlayer, self).__init__()

        self.last_visited_room = None # The room we were in last
        self.stop_on_exit = False # When we get to an exit, should we stop
        self.restart_on_exit = False # When we get to an exit, should we restart
        self.restart_attempts = 15 # How many times should we try to restart?

        self.visited_exits = {} # Exits we have been through for each room
        self.reverse_path = [] # Stack of directions to go to reverse progress
                               # inside the castle. A breadcrumb trail
        self.castle_exits = {} # If a room has an exit which leaves the castle,
                               # we store it here along with the direction we
                               # need to go in from that room to leave

        self.override_path = None # If set, the player will just follow the
                                  # the directions in this path till its done

        self.weapons, self.artifacts, self.treasure = [], [], [] # Inventory

    def next_move(self, location, items=None, threats=None):
        # The only way to be outside is to have explored there going forward.
        # We will never go outside by going backwards following our trail
        if location.is_outside or location.in_moat:
            return self.handle_outdoors()

        room_id = location.identity
        # This is the case where we have just entered the room after an
        # enter-randomly
        if self.restart_on_exit and not self.override_path:
            logging.info('Re-entered after an enter randomly')
            self.restart_attempts -= 1
            # If reset_on_exit is set, and the last_visited_room is this room,
            # have to exit again and try entering randomly again
            if self.last_visited_room == room_id:
                logging.info('Got to a room we already knew about. Exiting.')
                # We should try to start again if we have restart attempts left
                self.restart_on_exit = self.restart_attempts > 0
                # This is definately an exit, so we can look it up
                direction, _ = self.castle_exits[room_id]
                return '(go %s)' % direction
            # Otherwise, we have accomplished our goal of finding part of the
            # castle. We have no idea what exit we came through, so we have to
            # explore as normal
            else:
                logging.info('Got to a new part of the castle')
                self.restart_on_exit = False

        self.last_visited_room = room_id
        if room_id not in self.visited_exits:
            self.visited_exits[room_id] = set([])
        if self.reverse_path:
            door_entered = self.reverse_path[-1]
            self.visited_exits[room_id].add(door_entered)

        # If we have the frog, check to see if we are in an exit room. If so,
        # leave through that exit.
        if self.stop_on_exit and room_id in self.castle_exits:
            logging.info("Found an exit and we have the frog. Leaving.")
            direction, _ = self.castle_exits[room_id]
            return "(go %s)" % direction

        # Special handler case of just leaving
        # See below on where this comes from
        if self.override_path:
            direction = self.override_path.pop()
            logging.info("Following override path in direction %s" % direction)
            return '(go %s)' % direction

        # Possibly interact with the items in this room
        item_maybe = self.maybe_handle_items(items)
        if item_maybe:
            logging.info("Acting on items in room: %s" % item_maybe)
            return item_maybe

        logging.debug("HAS-FROG: %s" % self.stop_on_exit)

        unvisited = location.exits - self.visited_exits[room_id]
        # If this room has no exits we have not been through, go backwards by
        # following our breadcrumb trail
        if not unvisited:
            #TODO: Reconsider this case
            if len(self.reverse_path) == 0:
                # So, we are completely exhausted of places to explore, and our
                # backtrack list is empty. We have to be our origin. Frog or not
                # we should just leave. Unless the game is evil, we had to have
                # encountered atleast one exit. Get one, take the path from the
                # origin we stored, and follow that to the end
                logging.info("Cannot explore anymore. Finding exit to leave")
                # Tell the player he needs to enter randomly when he gets out
                # This detects hidden pieces of the castle
                self.restart_on_exit = True
                nearest_exit = self.find_nearest_exit()
                if not nearest_exit:
                    logging.error("We never encountered an exit. Que?")
                    return '(stop)'
                self.override_path = nearest_exit
                direction = self.override_path.pop()
                logging.info("Starting in direction %s" % direction)
            else:
                # We have not run out of places to reverse to, do go backwards
                direction = self.reverse_path.pop()
                logging.info("Backtracking on path in direction %s" % direction)
            return '(go %s)' % direction

        possible = list(unvisited)
        # We don't want to do anything in this room. We still have options to
        # explore, so choose the first one, record the reverse in our trail,
        # and move in that direction
        direction = possible[0]
        self.visited_exits[room_id].add(direction)
        reverse_direction = BreadcrumbPlayer.REVERSE_DIRECTIONS[direction]
        self.reverse_path.append(reverse_direction)
        logging.info("Going in direction %s" % direction)

        logging.debug("VISITED-ROOMS: %s" % len(self.visited_exits))
        logging.debug("FOUND-EXITS: %s" % len(self.castle_exits))
        logging.debug("BREADCRUMB-TRAIL: %s" % self.reverse_path)

        return "(go %s)" % direction

    def find_nearest_exit(self):
        ''' For each exit we have encountered, we have a path from the origin to
            that exit. What we can do is, using all those collected paths and
            the path we have back to the origin, compute the smallest combined
            path and take that to an exit.
            For best performance, while going back to the origin, we should
            check to see if we encounter any exits.
        '''
        if not self.castle_exits:
            return None
        shortest = None, None
        for exit_direction, exit_path in self.castle_exits.values():
            cur_short, _ = shortest
            length = len(exit_path)
            if not cur_short or length < cur_short:
                shortest = length, (exit_direction, exit_path)
        _, (leave, path) = shortest
        new_path = [leave] + \
                   self.invert_and_reverse_path(path) + \
                   self.reverse_path
        logging.debug("Calculated new exit path: %s" % new_path)
        return new_path

    def handle_outdoors(self):
        ''' Determines what to do when we are outside '''
        # If we have the frog, leave
        if self.stop_on_exit:
            return '(stop)'
        # If we were instructed to restart on exiting, do so
        if self.restart_on_exit:
            logging.info('Resetting and trying to enter randomly')
            self.reverse_path = []
            return '(enter-randomly)'
        # We have found the outside. The last room was an exit. Record this.
        # Since we cannot start outside, we can assume that reverse_path is non-
        # empty. We don't want to backtrack and leave the castle ever. So, we
        # remove the last entry in the reverse_path and go back in
        last_direction = self.reverse_path.pop()
        reverse_direction = BreadcrumbPlayer.REVERSE_DIRECTIONS[last_direction]
        logging.info("Found exit room: %s %s" %
                     (self.last_visited_room, reverse_direction))

        self.castle_exits[self.last_visited_room] = (reverse_direction,
                                                     self.reverse_path[:])
        return "(enter)"

    def maybe_handle_items(self, items):
        ''' Determines if we want to do anything with the given items.
            Returns None if we don't want to do anything
        '''
        # If we find the frog, pick his royal butt up
        if items and items.has_frog:
            logging.info("Found the frog. Taking it.")
            self.stop_on_exit = True
            self.override_path = self.find_nearest_exit()
            return '(carry (frog))'

        return None

    def invert_and_reverse_path(self, path):
        ''' Invert the order and direction of the directions in the given
            path
        '''
        inverted = [BreadcrumbPlayer.REVERSE_DIRECTIONS[d] for d in path]
        inverted.reverse()
        return inverted


if __name__ == '__main__':
    # When run as a python file, take all the docstrings and run them as tests
    import doctest
    doctest.testmod()
