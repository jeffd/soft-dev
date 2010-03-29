from castle import Castle, Location
from contextlib import closing
from json import loads
from optparse import OptionParser
from pexpect import spawn, TIMEOUT

# Extending spawn for recieve convience functions
class spawn(spawn):
    def receive_response(self, response_timeout, character_timeout):
        """ Receives characters until times out from
        no more being sent, returns string if it gets anything,
        throws Exception if it times out"""
        chars = []
        
        # Get first character, using initial response timeout
        try:
            chars.append(self.read_nonblocking(1,response_timeout))
        except TIMEOUT:
            raise Exception("Program timed out , didnt receive a response after \
                                        %f " % (response_timeout))
        
        # We've got at least one character of response
        # Get rest of response, using different (shorter) character timeout
        while True:
            try:
                char = self.read_nonblocking(1,character_timeout)
            except TIMEOUT:
                break

            chars.append(char)
        
        return ''.join(chars)

def encode_response(current_location, castle, response):
    # Add location to castle
    castle.add_visited_location(current_location)
    
    # Strip first line for decoding, it's either the Version number or the last move
    response = response[response.find('\n') + 1:len(response)]    
    return loads(response)

def next_move(current_location, castle, response):
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

# Get options from command line
parser = OptionParser()
parser.add_option("-l", "--larceny", dest="larceny", default="larceny",
                  help="Location of larceny binary", metavar="FILE")
parser.add_option("-g", "--game", dest="game", help="Location of game file")
parser.add_option("-c", "--charactertimeout", dest="character_timeout",
                  help="Time out for reading characters", type="float",
                  default=0.10)
parser.add_option("-r", "--responsetimeout", dest="response_timeout",
                  help="Timeout for total reading from shell", type="float",
                  default=4.00)
(options, args) = parser.parse_args()

# Get important options
character_timeout = options.character_timeout
response_timeout = options.response_timeout

# Make sure they specific a game
if options.game == None:
    parser.error("Please specify a game location, see --help for details")

# Setup command to execute program
process = '%s -r6rs -program %s' % (options.larceny, options.game)

# Setup objects
castle = Castle()
current_location = Location(0,0,0)

# Start process
with closing(spawn(process)) as child:
    # Start playing
    play_game = True
    
    # Make moves until you can't any more
    while play_game:
        # Get response
        response = child.receive_response(response_timeout, character_timeout)
        
        # Display response
        print response
        
        # Encode response
        response = encode_response(current_location, castle, response)
        
        print "Current location", current_location
        print "Visited Locations", castle.get_visited_locations()
        
        # Determine next move and update location
        move, current_location, play_game = next_move(current_location, castle, response)
        child.sendline(move)

