#from castle import Castle, Location
from contextlib import closing
from json import loads
from optparse import OptionParser
from pexpect import spawn, TIMEOUT
#from players import SimplePlayer
from player_new import BreadcrumbPlayer


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
#castle = Castle()
#current_location = Location(0,0,0)
player = BreadcrumbPlayer()

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
        # Strip first line for decoding, it's either the Version number or the last move
        response = response[response.find('\n') + 1:len(response)]
        response = loads(response)

        #print "Current location", player.current_location
        #print "Visited Locations", player.castle.get_visited_locations()

        # Determine next move and update location
        move, play_game = player.handle_response(response)
        child.sendline(move)

    # Receive last response
    response = child.read()
    print response
