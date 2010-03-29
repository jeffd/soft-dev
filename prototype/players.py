

class SimplePlayer:
    
    def next_move(self, current_location, castle, response):
        """ Function to determine next move, command to send
        and new location"""
    
        # Determine exits
        try:
            exits = response['location']['room']['exits']
        except (KeyError, TypeError):
            # FIXME: fix, make prettier, could be something else
            
            # No exits in dict, probably is an exit
            castle.add_exit(current_location)
            
            # FIXME: if we have the frog we're done
            # or maybe we should stop
            print 'Found exit'
            return '(stop)', current_location, False
        
        # We have exits, lets go somewhere we haven't been before
        unexplored_moves = castle.unexplored_moves(current_location, exits)
        if unexplored_moves == []:
            # No unexplored moves, just use first exit
            # TODO: improve
            direction_to_move = exits[0]
        else:
            # Use first unexplored move
            direction_to_move = unexplored_moves[0]
        
        # Go to first exit
        return ('(go %s)' % direction_to_move), \
                current_location.next_location(direction_to_move), True