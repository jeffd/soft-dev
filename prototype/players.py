

class SimplePlayer:
    
    def __init__(self, castle, current_location):
        self.castle = castle
        self.current_location = current_location
        self.castle.add_visited_location(current_location)
    
    def update_location(self, new_location):
        """ Updates current location and adds
        it to visited locations """
        # FIXME: this assumes we get a new response 
        # before actually receiving the response
        self.current_location = new_location
        self.castle.add_visited_location(new_location)
    
    def stuff_response(self, stuff):
        """ Returns message if we want to pickup anything,
        otherwise returns False """
        for thing in stuff:
            if ('treasure' in thing) and ('value' in thing):
                return '(carry (treasure "%s" %i))' \
                        % (thing['treasure'], thing['value'])
        
        return False
    
    def outside_response(self):
        """ Returns a message to send if we're outside
        the moat """
        self.castle.add_exit(self.current_location)
        
        # FIXME: if we have the frog we're done
        # or maybe we should stop
        print 'Found exit'
        return '(stop)', False
    
    def room_response(self, room):
        # Get list of exits
        exits = room['exits']
        
        # Lets try to go somewhere we haven't been before
        unexplored_moves = self.castle.unexplored_moves(self.current_location, exits)
        if unexplored_moves == []:
            # No unexplored moves, just use first exit
            # TODO: improve
            direction_to_move = exits[0]
        else:
            # Use first unexplored move
            direction_to_move = unexplored_moves[0]
        
        # Save new current position
        new_location = self.current_location.next_location(direction_to_move)
        self.update_location(new_location)
        
        # Go to first exit
        return ('(go %s)' % direction_to_move), True
        
    def next_move(self, response):
        """ Function to determine next move, command to send
        and new location"""
        
        # Determine if we want to pickup objects
        if 'stuff' in response:
            message_to_send = self.stuff_response(response['stuff'])
            if message_to_send:
                return message_to_send, True
        
        # Make sure we have a location
        if not ('location' in response):
            raise Exception("Location not found in response")
        
        # Response for outside the moat
        if response['location'] == "outside the castle":
            return self.outside_response()
        
        # Response for in the moat
        if response['location'] == "in the moat":
            # FIXME: What does in the moat mean?
            raise Exception("Don't understand what to do in the moat")
        
        # Default room response
        return self.room_response(response['location']['room'])