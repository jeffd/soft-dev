from contextlib import closing
from json import loads
from pexpect import spawn, TIMEOUT


# Extending spawn for recieve convience functions
class spawn(spawn):
    def receive_response(self, timeout = 0.25):
        """ Receives characters until times out from
        no more being sent """
        chars = []

        while True:
            try:
                char = self.read_nonblocking(1,timeout)
            except TIMEOUT:
                break

            chars.append(char)
        
        return ''.join(chars)

def next_move(response):
    """ Function to determine next move """
    # Encode into python dict
    response_object = loads(response)
    
    # Determine exits
    try:
        exits = response_object['location']['room']['exits']
    except (KeyError, TypeError):
        # No exits in dict, don't know what to do!
        return False
    
    # Go to first exit
    return ('(go %s)' % exits[0])

larceny = 'larceny -r6rs -program'
game_location = '/course/cs4500wc/Assignments/Game5/game.sps.slfasl'

process = '%s %s' %(larceny, game_location)

# Start process
with closing(spawn(process)) as child:

    # Start playing
    play_game = True
    
    # Make moves until you can't any more
    while play_game:
        # Get response
        response = child.receive_response()
        # Display response
        print response
        # Strip first line for decoding, it's either the Version number or the last move
        response = response[response.find('\n') + 1:len(response)]    
        
        # Send next move
        move = next_move(response)
        if move == False:
            print "No exits, don't know what to do"
            break
    
        child.sendline(move)
