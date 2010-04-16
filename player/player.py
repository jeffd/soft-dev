''' Various implementations of the Player class.
'''
import logging

from player_util import Player

__all__ = ['BreadcrumbPlayer',
           'SelfPreservationPlayer',
           'GreedyPlayer',
           'FighterPlayer',
           'GoldDigger']

# Through numerous trials, we discovered the following weapons and treasure
# to not be worth picking up
IGNORED_WEAPONS = set(["hi there",
                       "atomic",
                       "grenade launcher"])

IGNORED_TREASURE = set(["art"])


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
        ''' Determines what to do in the given location with the given items
            and threats around us
        '''
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
            logging.info("SETTING-ORIGIN: %s" % room_id)
            self.last_origin = room_id
            self.exit_paths[room_id] = []

        # Make sure we are tracking the doors we use in this room
        if room_id not in self.visited_doors:
            self.visited_doors[room_id] = set([])

        # Make sure that if we came from somewhere, we mark the entered door
        if self.reverse_path:
            door_entered = self.reverse_path[-1]
            self.visited_doors[room_id].add(door_entered)

        # If we have the frog, check to see if we are in an exit room. If so,
        # leave through that exit.
        if self.stop_on_exit and room_id in self.castle_exits:
            logging.info("Found an exit and we have the frog. Leaving.")
            direction = self.castle_exits[room_id]
            return "(go %s)" % direction

        # Possibly interact with attackers in this room
        attack_maybe = self.maybe_handle_attack(location, items, threats)
        if attack_maybe:
            logging.info("Acting on attackers in the room: %s" % attack_maybe)
            return attack_maybe

        # Special handler case of just leaving
        # See below on where this comes from
        if self.override_path:
            direction = self.override_path.pop()
            logging.info("Following override path in direction %s" % direction)
            return '(go %s)' % direction

        # Possibly interact with the items in this room
        item_maybe = self.maybe_handle_items(location, items, threats)
        if item_maybe:
            logging.info("Acting on items in room: %s" % item_maybe)
            return item_maybe

        logging.debug("HAS-FROG: %s" % self.stop_on_exit)

        # If we haven't acted on anything else, just do some old
        # fashion exploring
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
        new_path = min(exit_paths, key=len) + self.reverse_path
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
        logging.info("Found exit room: %s" % self.last_visited_location)
        logging.debug("-- direction and path: %s, %s" % (reverse_direction,
                                                         self.reverse_path))

        self.castle_exits[self.last_visited_location] = reverse_direction
        origin_to_outside = [reverse_direction] + \
                BreadcrumbPlayer.invert_and_reverse_path(self.reverse_path)
        self.exit_paths[self.last_origin].append(origin_to_outside)

        return "(enter)"

    def maybe_handle_items(self, location, items, threats):
        ''' Determines if we want to do anything with the given items.
            Returns None if we don't want to do anything
        '''
        # If we find the frog, pick his royal butt up
        if items.has_frog:
            logging.info("Found the frog. Taking it.")
            self.stop_on_exit = True
            self.override_path = self.find_nearest_outdoors()
            return self.carry_frog()

        return None

    def maybe_handle_attack(self, location, items, threats):
        ''' Determines if we want to do anything pertaining to attacking
            in the given room. Returns None if we don't want to do
            anything
        '''
        return None

    @staticmethod
    def invert_and_reverse_path(path):
        ''' Invert the order and direction of the directions in the given
            path
        '''
        inverted = [BreadcrumbPlayer.REVERSE_DIRECTIONS[d] for d in path]
        inverted.reverse()
        return inverted


class SelfPreservationPlayer(BreadcrumbPlayer):
    ''' An implementation of Breadcrumb player which actively defends itself
        from any type of harm.
        It will seak out the best weapon it can find. Once it has one, it will
        attack anything which attacks it in order to survive.
        It will also collect all the treasure it can hold. If it gets a little
        overweight, it will drop and ignore treasures till it can continue
        without taking harm.
        Otherwise, this player falls back to the Breadcrumb class, exploring
        and looking for the frog.
    '''
    def __init__(self):
        super(SelfPreservationPlayer, self).__init__()
        self._dropped_items = set([]) # Items we have dropped in a room

    @property
    def current_weapon(self):
        ''' Returns either the first weapon we have, or None '''
        return self.weapons and self.weapons[0] or None

    def maybe_handle_attack(self, location, items, threats):
        ''' If we are being attacked, attack them back!
        '''
        if threats.attacked:
            if self.current_weapon:
                return '(attack (%s) (weapon "%s" %s))' % \
                    (" ".join(map(lambda x: '"%s"' % x, threats.attacked_by)),
                     self.current_weapon[0],
                     self.current_weapon[1])
            else:
                return '(attack (%s))' % \
                    " ".join(map(lambda x: '"%s"' % x, threats.attacked_by))
        return None


    def maybe_handle_items(self, location, items, threats):
        ''' Determines what to do when considering items in the room '''

        # Always check for the frog first
        frog_maybe = super(SelfPreservationPlayer, self)\
                .maybe_handle_items(location, items, threats)
        if frog_maybe:
            return frog_maybe

        # If we are being attacked, ignore all items and get the hell out
        if threats.attacked:
            return None

        # If we are tired and have treasures or weapon, start getting rid of it
        if threats.tired and self.treasure + self.weapons:
            # Subtract the current tiredness from the previous
            difference = self.prev_tired - threats.tired

            # If our tiredness is not increasing, drop treasure to get better
            if self.treasure:
                if difference >= 0:
                    # If we didn't drop an artifact, drop the smallest treasure
                    # Find treasure with smallest value
                    smallest_treasure = min(self.treasure, key=lambda x: x[1])

                    # Add to list noting to not pick this item up again
                    self._dropped_items.add(smallest_treasure)
                    return self.drop_treasure(smallest_treasure)
            else: # Otherwise, we have to drop our weapon
                self.drop_weapon(self.current_weapon)

        # First, we look for a new and better weapon
        fweapons = filter(lambda x: x[0] not in IGNORED_WEAPONS, items.weapons)
        if fweapons:
            best_name, best_lethality = max(fweapons, key=lambda x: x[1])
            if not self.current_weapon:
                return self.carry_weapon((best_name, best_lethality))
            else:
                cur_name, cur_lethality = self.current_weapon
                if cur_lethality < best_lethality:
                    return self.drop_weapon((cur_name, cur_lethality))

        # Next, we start picking up all treasures we find
        # We keep track of the items we drop in a room, as to not get into
        # an infinite loop of dropping and picking back up
        moved = self.last_visited_location == location.identity
        if moved and not location.is_outside:
            logging.debug("PREVIOUS-LOC: " + str(self.last_visited_location))
            logging.debug("NEW-LOC: " + str(location.identity))
            logging.debug("Entered new room. Resetting ignore.")
            self._dropped_items = set([])

        if items.treasures:
            for treasure in sorted(items.treasures, lambda x, y: y[1] - x[1]):
                name, _ = treasure
                dropped = treasure in self._dropped_items
                if not dropped and name not in IGNORED_TREASURE:
                    return self.carry_treasure(treasure)
#        # Pick up artifacts too
#        if items.artifacts:
#            for artifact in items.artifacts:
#                if artifact not in self._dropped_items:
#                    return self.carry_artifact(artifact)

        return None


### EVERYTHING WHICH FOLLOWS IS FOR TESTING PURPOSES
class GreedyPlayer(BreadcrumbPlayer):

    def maybe_handle_items(self, location, items, threats):
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

    def maybe_handle_items(self, location, items, threats):
        filtered = filter(lambda x: x[0] not in IGNORED_WEAPONS, items.weapons)
        if filtered:
            best_name, best_lethality = max(filtered, key=lambda x: x[1])
            if not self.current_weapon:
                return self.carry_weapon((best_name, best_lethality))
            else:
                cur_name, cur_lethality = self.current_weapon
                if cur_lethality < best_lethality:
                    return self.drop_weapon((cur_name, cur_lethality))
        return super(FighterPlayer, self).maybe_handle_items(items)

    def next_move(self, location, items, threats):

        if threats.attacked and self.current_weapon:
            return '(attack (%s) (weapon "%s" %s))' % \
                    (" ".join(map(lambda x: '"%s"' % x, threats.attacked_by)),
                     self.current_weapon[0],
                     self.current_weapon[1])

        return super(FighterPlayer, self).next_move(location, items, threats)


class GoldDigger(BreadcrumbPlayer):

    def __init__(self):
        self._dropped_items = set([])
        super(GoldDigger, self).__init__()

    def next_move(self, location, items=None, threats=None):
        # Reset ignored treasure if we're in a new room and not outside
        moved = self.last_visited_location == location.identity
        if moved and not location.is_outside:
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

            # If our tiredness is not increasing, drop stuff to get better
            if difference >= 0:
#                # First drop the first artifact
#                if self.artifacts:
#                    dropping = self.artifacts[0]
#                    self._dropped_items.add(dropping)
#                    return self.drop_artifact(self.artifacts[0])

                # If we didn't drop an artifact, drop the smallest treasure
                # Find treasure with smallest value
                smallest_treasure = min(self.treasure, key=lambda x: x[1])

                # Add to list noting to not pick this item up again
                self._dropped_items.add(smallest_treasure)
                return self.drop_treasure(smallest_treasure)

        # Otherwise, pick up treasure
        if items.treasures:
            for treasure in sorted(items.treasures, lambda x, y: y[1] - x[1]):
                name, _ = treasure
                dropped = treasure in self._dropped_items
                if not dropped and name not in IGNORED_TREASURE:
                    return self.carry_treasure(treasure)
#        # Pick up artifacts too
#        if items.artifacts:
#            for artifact in items.artifacts:
#                if artifact not in self._dropped_items:
#                    return self.carry_artifact(artifact)

        return super(GoldDigger, self).next_move(location, items, threats)


if __name__ == '__main__':
    # When run as a python file, take all the docstrings and run them as tests
    import doctest
    doctest.testmod()
