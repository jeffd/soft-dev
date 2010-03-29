

class SimplePlayer:
    
    def __init__(self, castle, current_location):
        self.castle = castle
        self.current_location = current_location
        self.castle.add_visited_location(current_location)
    
    def next_move(self, response):
        """ Function to determine next move, command to send
        and new location"""
    
        # Determine exits
        try:
            exits = response['location']['room']['exits']
        except (KeyError, TypeError):
            # FIXME: fix, make prettier, could be something else
            
            # No exits in dict, probably is an exit
            self.castle.add_exit(self.current_location)
            
            # FIXME: if we have the frog we're done
            # or maybe we should stop
            print 'Found exit'
            return '(stop)', False
        
        # We have exits, lets go somewhere we haven't been before
        unexplored_moves = self.castle.unexplored_moves(self.current_location, exits)
        if unexplored_moves == []:
            # No unexplored moves, just use first exit
            # TODO: improve
            direction_to_move = exits[0]
        else:
            # Use first unexplored move
            direction_to_move = unexplored_moves[0]
        
        # Save new current position
        # FIXME: this assumes we get a new response before actually receiving
        # the response
        new_location = self.current_location.next_location(direction_to_move)
        self.current_location = new_location
        self.castle.add_visited_location(new_location)
        
        # Go to first exit
        return ('(go %s)' % direction_to_move), True