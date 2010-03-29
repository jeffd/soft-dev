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
        
        # Strip first line for decoding, it's either the Version number or the last move
        response = response[response.find('\n') + 1:len(response)]    
        
        # Send next move
        move = next_move(response)
        if move == False:
            print "No exits, don't know what to do"
            break
    
        child.sendline(move)
