"""
This program emulates the game playing program, by using a castle file defined
with multiple rooms like:

<castle>
    <room>
        <location>
            <floor>0</floor>
            <x>0</x>
            <y>0</y>
        </location>
        <message>
            { "actors" : [ [ "minion" ,
                         "unworthy" ] ] ,
            "location" : { "room" : { "purpose" : "gallery" ,
                                      "attributes" : [ "bare-floor" ,
                                                       "stone" ,
                                                       "fireplace south" ] ,
                                      "exits" : [ "east" ] } } }
        </message>
    </room>
</castle>

"""
from castle import Location
from json import loads
from optparse import OptionParser
from xml.etree import ElementTree

# Get options from command line
parser = OptionParser()
parser.add_option("-c", "--castle", dest="castle_file",
                  help="Location of castle file to use", metavar="FILE")
(options, args) = parser.parse_args()

if options.castle_file == None:
    parser.error('Please specify a castle to use')

class Room:
    
    def __init__(self, location, message):
        self.location = location
        self.message = message
    
    def __repr__(self):
        return 'Location %s, Message %s' % (str(self.location), self.message)
    
    def get_message(self):
        return self.message

    def print_message(self):
        print self.message

class DummyCastle:
    
    def __init__(self):
        self.list_of_rooms = []
    
    def add_room(self, room):
        self.list_of_rooms.append(room)
    
    def find_room(self, location):
        for room in self.list_of_rooms:
            if room.location == location:
                return room
        
        return False

dummy_castle = DummyCastle()

# Open file, create locations in dummy castle
with open(options.castle_file, 'r') as castle_file:
    castle_as_string = castle_file.read()
    
    et = ElementTree.fromstring(castle_as_string)
    rooms = et.findall('room')
    
    for room in rooms:
        location = room.find('location')
        message = room.find('message').text.strip()
        
        location_convert = lambda x: int(location.find(x).text.strip())
        location = Location(location_convert('floor'),
                             location_convert('x'),
                             location_convert('y'))
        room = Room(location, message)
        
        dummy_castle.add_room(room)

print "Version Test"
current_room = dummy_castle.find_room(Location(0,0,0))
current_room.print_message()

collect_input = True
while collect_input:
    input = raw_input("")
    
    # Convert message
    response = loads(current_room.message)
    
    # See if they are going to go to an exit
    if ("location" in response) and ("room" in response['location']) \
        and ("exits" in response["location"]["room"]):
        
        exits = response["location"]["room"]["exits"]
        for exit in exits:
            if input == ('(go %s)' % (exit)):
                new_location = current_room.location.next_location(exit)
                current_room = dummy_castle.find_room(new_location)
                current_room.print_message()
                continue
    
    # See if they want to pickup anything
    if "stuff" in response:
        for stuff in response['stuff']:

            if 'treasure' in stuff.keys():
                if input == '(carry (treasure "%s" %i))' % \
                                    (stuff['treasure'], \
                                     stuff['value']):
                    
                    # TODO: delete carried treasure
                    current_room.print_message()
                    continue
    
    
    
    