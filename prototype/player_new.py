
class Location(object):

    @classmethod
    def from_json(cls, location):
        if location == "outside the castle":
            return Outside()
        elif location == "in the moat":
            return InMoat()
        else:
            room = location['room']
            return Room(room)

    @property
    def identity(self):
        return "NOTHING"

    @property
    def is_outside(self):
        return False

    @property
    def in_moat(self):
        return False

    @property
    def exits(self):
        return frozenset([])

    def __eq__(self, other):
        return hasattr(other, "identity") and self.identity == other.identity


class Room(Location):

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

    @property
    def identity(self):
        return "OUTSIDE"

    @property
    def is_outside(self):
        return True


class InMoat(Location):

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

    def __init__(self):
        self.move_count = -1 # How many moves we have made so far

    def handle_response(self, json):
        ''' Converts the given json into useable objects and
            then call next_move to determine what to do
        '''
        location, items, threats = None, None, None
        location = Location.from_json(json['location'])
        if 'stuff' in json:
            items = Items(json['stuff'])
        if 'threats' in json:
            pass

        self.move_count += 1
        return self.next_move(location, items, threats)

    def next_move(self, location, items=None, threats=None):
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

    def __init__(self, quick_exit=15):
        super(BreadcrumbPlayer, self).__init__()

        self.last_visited_room = None # The room we were in last
        self.visited_exits = {} # Exits we have been through for each room
        self.reverse_path = [] # Stack of directions to go to reverse progress
                               # inside the castle. A breadcrumb trail
        self.castle_exits = {} # If a room has an exit which leaves the castle,
                               # we store it here along with the direction we
                               # need to go in from that room to leave

        self.override_path = None # If set, the player will just follow the
                                  # the directions in this path till its done

        self.quick_exit = quick_exit # Minimum number of moves needed to keep
                                     # exploring after finding an exit

        self.weapons, self.artifacts, self.treasure = [], [], [] # Inventory
        self.has_frog = False # Do we have the frog yet

    def next_move(self, location, items=None, threats=None):
        # The only way to be outside is to have explored there going forward.
        # We will never go outside by going backwards following our trail
        if location.is_outside or location.in_moat:
            return self.handle_outdoors()

        # Special handler case of just leaving
        # See below on where this comes from
        if self.override_path:
            print "===== FOLLOWING OVERRIDE PATH ===="
            direction = self.override_path.pop()
            return '(go %s)' % direction, True

        # Possibly interact with the items in this room
        item_maybe = self.maybe_handle_items(items)
        if item_maybe:
            print "===== ACTING ON ITEM ===="
            return item_maybe

        print "==== HAVE FROG? :", self.has_frog

        room_id = location.identity
        self.last_visited_room = room_id
        # If we have the frog, check to see if we are in an exit room. If so,
        # leave through that exit.
        if self.has_frog and room_id in self.castle_exits:
            direction, _ = self.castle_exits[room_id]
            return "(go %s)" % direction, True

        if room_id not in self.visited_exits:
            self.visited_exits[room_id] = set([])
        unvisited = location.exits - self.visited_exits[room_id]
        # If this room has no exits we have not been through, go backwards by
        # following our breadcrumb trail
        if not unvisited:
            #TODO: Reconsider this case
            if len(self.reverse_path) == 0:
                # So, we are completely exhausted of places to explore, and our
                # backtrack list is empty. We have to be our origin. If we have the
                # frog or not, we should just leave. Unless the game is evil, we had
                # to have encountered atleast one exit. Get one, take the path from
                # the origin we stored, and follow that to the end
                # Just try exiting first
                self.has_frog = True
                if room_id in self.castle_exits:
                    direction, _ = self.castle_exits[room_id]
                else:
                    print "===== EXCEPTIONAL CASE ====="
                    # Convince the player he has a frog, so he leaves the castle
                    exit_dir, path = self.castle_exits.values()[0]
                    exit_path = [exit_dir] + self.invert_and_reverse_path(path)
                    self.override_path = exit_path
                    direction = self.override_path.pop()
            else:
                print "===== GOING BACKWARDS ON PATH ====="
                # We have not run out of places to reverse to, do go backwards
                direction = self.reverse_path.pop()
            return '(go %s)' % direction, True

        possible = list(unvisited)
        # We don't want to do anything in this room. We still have options to
        # explore, so choose the first one, record the reverse in our trail,
        # and move in that direction
        direction = possible[0]
        self.visited_exits[room_id].add(direction)
        reverse_direction = BreadcrumbPlayer.REVERSE_DIRECTIONS[direction]
        self.reverse_path.append(reverse_direction)

        print "==== VISITED ROOMS:", len(self.visited_exits)
        print "==== FOUND EXITS:", self.castle_exits
        return "(go %s)" % direction, True

    def handle_outdoors(self):
        ''' Determines what to do when we are outside '''
        # If we have the frog, or found the exit quickly, just leave
        if self.has_frog or self.move_count <= self.quick_exit:
            return '(stop)', False
        # We have found the outside. The last room was an exit. Record this.
        # Since we cannot start outside, we can assume that reverse_path is non-
        # empty. We don't want to backtrack and leave the castle ever. So, we
        # remove the last entry in the reverse_path and go back in
        print "===== FOUND EXIT! ====="
        last_direction = self.reverse_path.pop()
        reverse_direction = BreadcrumbPlayer.REVERSE_DIRECTIONS[last_direction]
        self.castle_exits[self.last_visited_room] = (reverse_direction, [])
        return "(enter)", True

    def maybe_handle_items(self, items):
        ''' Determines if we want to do anything with the given items.
            Returns None if we don't want to do anything
        '''
        # If we find the frog, pick his royal butt up
        if items and items.has_frog:
            self.has_frog = True
            return '(carry (frog))', True
        return None

    def invert_and_reverse_path(self, path):
        ''' Invert the order and direction of the directions in the given
            path
        '''
        inverted = [BreadcrumbPlayer.REVERSE_DIRECTIONS[d] for d in path]
        inverted.reverse()
        return inverted


