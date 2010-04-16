''' The player module contains the classes necessary to correctly traverse the
    dungeon.
'''
import logging

__all__ = ['Location', 'Player', 'BreadcrumbPlayer', 'GreedyPlayer']

# Through numerous trials, we discovered the following weapons and treasure
# to not be worth picking up
IGNORED_WEAPONS = set(["hi there",
                       "atomic",
                       "grenade launcher"])
IGNORED_TREASURE = set(["art"])

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
                self._artifacts.append((item['artifact'], tuple(item['description'])))

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

        # Assign null values to indicate we haven't received anything
        self._ill, self._tired, self._injured, self._attacked, self._attacked_by = \
            None, None, None, None, None

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
        converted into the proper objects. These objects are passed to the next_move
        method, whose implementation is left up to the implementing class. After
        the implementing class decides on a move, the last room seen and changes
        in health are recorded.
    '''

    def __init__(self):
        self.prev_health, self.prev_tired, self.prev_ill = 9, 9, 9 # Statuses
        self.weapons, self.artifacts, self.treasure = [], [], []   # Inventory
        self.last_visited_location = None   # The location we saw last

    def handle_response(self, json):
        ''' Converts the given json into useable objects. Returns either a string,
            which is sent to the dungeon program, or False to indicate to stop
            playing
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

    # Carry functions
    def carry_weapon(self, weapon):
        return self.make_carry_message("weapon", weapon, self.weapons)

    def carry_treasure(self, treasure):
        return self.make_carry_message("treasure", treasure, self.treasure)

    def carry_artifact(self, artifact):
        return self.make_carry_message("artifact", artifact, self.artifacts)

    # Drop functions
    def drop_weapon(self, weapon):
        return self.make_drop_message("weapon", weapon, self.weapons)

    def drop_treasure(self, treasure):
        return self.make_drop_message("treasure", treasure, self.treasure)

    def drop_artifact(self, artifact):
        return self.make_drop_message("artifact", artifact, self.artifacts)

    def make_carry_message(self, item_type, item, inv):
        ''' Add an item to one of our inventories when we carry it '''
        inv.append(item)

        return self.make_message("carry", item_type, item)

    def make_drop_message(self, item_type, item, inv):
        ''' Remove an item to one of our inventories when we drop it '''
        inv.remove(item)

        # Drop it like its hot
        return self.make_message("drop", item_type, item)

    def make_message(self, action, item_type, item):
        ''' Returns a message for carrying an object '''

        if item_type == "frog":
            return "(%s (frog))" % action

        name, etc = item
        if item_type == "artifact":
            etc = " ".join(map(lambda x: '"%s"' % x, etc))

        return "(%s (%s \"%s\" %s))" % (action, item_type, name, etc)

    def ignore_weapons(self, weapon):
        return weapon[0] not in IGNORED_WEAPONS


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

        self.stop_on_exit = False # When we get to an exit, should we stop
        self.restart_on_exit = False # When we get to an exit, should we restart

        self.visited_doors = {} # Doors we have been through for each room
        self.reverse_path = [] # Stack of directions to go to reverse progress
                               # inside the castle. A breadcrumb trail
        self.castle_exits = {} # If a room has an exit which leaves the castle,
                               # we store it here along with the direction we
                               # need to go in from that room to leave
        self.last_origin = None # The room id of the last room we considered the
                                # origin of the castle
        self.exit_paths = {}    # Maps room ids to paths to exits.

        self.override_path = None # If set, the player will just follow the
                                  # the directions in this path till its done

    def next_move(self, location, items, threats):
        # The only way to be outside is to have explored there going forward.
        # We will never go outside by going backwards following our trail
        if location.is_outside or location.in_moat:
            return self.handle_outdoors()

        room_id = location.identity

        # This is the case where we have just entered the room after an
        # enter-randomly
        if self.restart_on_exit and not self.override_path:
            logging.info('Re-entered after an enter randomly')
            if room_id in self.visited_doors:
                logging.info('Got to a room we already knew about. Exiting.')
                # This is definately an exit, so we can look it up
                direction = self.castle_exits[room_id]
                return '(go %s)' % direction
            # Otherwise, we have accomplished our goal of finding part of the
            # castle. We have no idea what exit we came through, so we have to
            # explore as normal
            else:
                logging.info('Got to a new part of the castle')
                self.restart_on_exit = False
                self.last_origin = None

        # When we first start exploring, we need to set this room as the origin
        if not self.last_origin:
            logging.debug("SETTING-ORIGIN: %s" % room_id)
            self.last_origin = room_id
            self.exit_paths[room_id] = []

        if room_id not in self.visited_doors:
            self.visited_doors[room_id] = set([])
        if self.reverse_path:
            door_entered = self.reverse_path[-1]
            self.visited_doors[room_id].add(door_entered)

        # If we have the frog, check to see if we are in an exit room. If so,
        # leave through that exit.
        if self.stop_on_exit and room_id in self.castle_exits:
            logging.info("Found an exit and we have the frog. Leaving.")
            direction = self.castle_exits[room_id]
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

        unvisited = location.exits - self.visited_doors[room_id]
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
                nearest_outdoors = self.find_nearest_outdoors()
                if not nearest_outdoors:
                    logging.error("We never encountered an exit. Que?")
                    return '(stop)'
                self.override_path = nearest_outdoors
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
        self.visited_doors[room_id].add(direction)
        reverse_direction = BreadcrumbPlayer.REVERSE_DIRECTIONS[direction]
        self.reverse_path.append(reverse_direction)
        logging.info("Going in direction %s" % direction)

        logging.debug("VISITED-ROOMS: %s" % len(self.visited_doors))
        logging.debug("FOUND-EXITS: %s" % len(self.castle_exits))
        #logging.debug("CURRENT-ORIGIN: %s" % self.last_origin)
        #logging.debug("PATHS-TO-EXITS: %s" % self.exit_paths[self.last_origin])
        #logging.debug("BREADCRUMB-TRAIL: %s" % self.reverse_path)

        return "(go %s)" % direction

    def find_nearest_outdoors(self):
        ''' For each exit we have encountered, we have a path from the origin to
            that exit. What we can do is, using all those collected paths and
            the path we have back to the origin, compute the smallest combined
            path and take that to an exit.
            For best performance, while going back to the origin, we should
            check to see if we encounter any exits.
        '''
        # Get the list of exit paths for the current origin
        exit_paths = self.exit_paths[self.last_origin]
        if not exit_paths:
            return None
        new_path = min(exit_paths, key=lambda x: len(x)) + self.reverse_path
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
        logging.info("Found exit room: %s, %s, %s" %
            (self.last_visited_location, reverse_direction, self.reverse_path))

        self.castle_exits[self.last_visited_location] = reverse_direction
        origin_to_outside = [reverse_direction] + \
                            self.invert_and_reverse_path(self.reverse_path)
        self.exit_paths[self.last_origin].append(origin_to_outside)

        return "(enter)"

    def maybe_handle_items(self, items):
        ''' Determines if we want to do anything with the given items.
            Returns None if we don't want to do anything
        '''
        # If we find the frog, pick his royal butt up
        if items.has_frog:
            logging.info("Found the frog. Taking it.")
            self.stop_on_exit = True
            self.override_path = self.find_nearest_outdoors()
            return '(carry (frog))'

        return None

    def invert_and_reverse_path(self, path):
        ''' Invert the order and direction of the directions in the given
            path
        '''
        inverted = [BreadcrumbPlayer.REVERSE_DIRECTIONS[d] for d in path]
        inverted.reverse()
        return inverted

class GreedyPlayer(BreadcrumbPlayer):

    def maybe_handle_items(self, items):
        maybe = super(GreedyPlayer, self).maybe_handle_items(items)

        if maybe:
            return maybe

        # Pickup everything because we're greedy as hell
        message = None
        if items.weapons:
            item = items.weapons[0]
            name, leathality = items.weapons[0]
            # TODO: don't put "hi there" in items
            if not(name == "hi there"):
                message = self.carry_weapon(item)
        elif items.treasures:
            item = items.treasures[0]
            message = self.carry_treasure(item)
        elif items.artifacts:
            item = items.artifacts[0]
            message = self.carry_artifact(item)

        if message:
            logging.debug("picking up item %s" % message)
            return message

        return None

class FighterPlayer(BreadcrumbPlayer):

    @property
    def current_weapon(self):
        if not self.weapons:
            return None
        return self.weapons[0]

    def maybe_handle_items(self, items):
        valid_weapons = filter(self.ignore_weapons, items.weapons)
        if valid_weapons:
            best_name, best_lethality = max(valid_weapons, key=lambda x: x[1])
            if not self.current_weapon:
                return self.carry_weapon((best_name, best_lethality))
            else:
                cur_name, cur_lethality = self.current_weapon
                if cur_lethality < best_lethality:
                    return self.drop_weapon((cur_name, cur_lethality))
        return super(FighterPlayer, self).maybe_handle_items(items)

    def next_move(self, location, items, threats):

        if threats.attacked and self.current_weapon:
            return '(attack (%s) (weapon "%s" %s))' % (" ".join(map(lambda x: '"%s"' % x, threats.attacked_by)),
                                                      self.current_weapon[0],
                                                      self.current_weapon[1])

        return super(FighterPlayer, self).next_move(location, items, threats)

class GoldDigger(BreadcrumbPlayer):

    def __init__(self):
        self._dropped_items = set([])
        super(GoldDigger, self).__init__()

    def next_move(self, location, items=None, threats=None):
        # Reset ignored treasure if we're in a new room and not outside
        if (self.last_visited_location != location.identity) and not location.is_outside:
            logging.debug("PREVIOUS-LOC: " + str(self.last_visited_location))
            logging.debug("NEW-LOC: " + str(location.identity))
            logging.debug("Entered new room. Resetting ignore.")
            self._dropped_items = set([])

        logging.debug("IGNORED-ITEMS: " + str(self._dropped_items))
        # TODO: This only drops treasure, does not include weapons. Change
        # this upon merge
        if threats.tired and self.treasure:
            # Subtract the current tiredness from the previous
            difference = self.prev_tired - threats.tired
            
            # If our tiredness is not increasing aka we're not getting better, drop stuff
            if difference >= 0:
                '''
                # First drop the first artifact
                if self.artifacts:
                    dropping = self.artifacts[0]
                    self._dropped_items.add(dropping)
                    return self.drop_artifact(self.artifacts[0])
                '''
                
                # If we didn't drop an artifact, drop the smallest treasure
                # Find treasure with smallest value
                smallest_treasure = sorted(self.treasure, key = lambda x: x[1])[0]
                
                # Add to list noting to not pick this item up again
                self._dropped_items.add(smallest_treasure)
                return self.drop_treasure(smallest_treasure)

        # Otherwise, Pickup treasure
        if items.treasures:
            for treasure in sorted(items.treasures, lambda x, y: y[1] - x[1]):
                name, _ = treasure
                if treasure not in self._dropped_items and name not in IGNORED_TREASURE:
                    return self.carry_treasure(treasure)
        """
        # Pick up artifacts too
        if items.artifacts:
            for artifact in items.artifacts:
                if artifact not in self._dropped_items:
                    return self.carry_artifact(artifact)
        """

        return super(GoldDigger, self).next_move(location, items, threats)

if __name__ == '__main__':
    # When run as a python file, take all the docstrings and run them as tests
    import doctest
    doctest.testmod()
