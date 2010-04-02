"""
This program emulates the game playing program, by using a castle file defined
with multiple rooms like:

<castle>
    <room id="A">
        <message>
            { "actors" : [ [ "minion" ,
                         "unworthy" ] ] ,
            "stuff" : [ { "frog" : [ ] } ],
            "location" : { "room" : { "purpose" : "gallery" ,
                                      "attributes" : [ "bare-floor" ,
                                                       "stone" ,
                                                       "fireplace south" ] ,
                                      "exits" : [ <exits> ] } } }
        </message>
        <exits>
            <east>B</east>
        </exits>
    </room>
    <room id="B">
        <message>
            { "actors" : [ [ "minion" ,
                         "unworthy" ] ] ,
            "stuff" : [ { "frog" : [ ] } ],
            "location" : { "room" : { "purpose" : "gallery" ,
                                      "attributes" : [ "bare-floor" ,
                                                       "stone" ,
                                                       "fireplace south" ] ,
                                      "exits" : [ <exits> ] } } }
        </message>
        <exits>
            <west>A</west>
            <east>C</east>
        </exits>
    </room>
    <room id="C">
        {"location" : "outside the castle"}
    </room>
</castle>

"""
from json import loads, JSONEncoder
from optparse import OptionParser
from xml.etree import ElementTree

import sys

# Get options from command line
parser = OptionParser()
parser.add_option("-c", "--castle", dest="castle_file",
                  help="Location of castle file to use", metavar="FILE")
(options, args) = parser.parse_args()

if options.castle_file == None:
    parser.error('Please specify a castle to use')

class DummyRoom:
    
    def __init__(self, id, message, exits):
        self.id = id
        self.message = message
        # exits is a dict exits["east"] = "A"
        self.exits = exits
    
    def __repr__(self):
        return 'Room %s Exits %s' % (self.id, str(self.exits))
    
    def set_message(self, message):
        self.message = message
        
    def get_message(self):
        return self.message

    def print_message(self):
        print self.message

class DummyCastle():
    
    def __init__(self):
        self.list_of_rooms = []
    
    def add_room(self, room):
        self.list_of_rooms.append(room)
    
    def find_room(self, room_id):
        for room in self.list_of_rooms:
            if room.id == room_id:
                return room
        return False
    
    def get_room_by_index(self, index):
        return self.list_of_rooms[index]

dummy_castle = DummyCastle()

# Open file, create locations in dummy castle
with open(options.castle_file, 'r') as castle_file:
    castle_as_string = castle_file.read()
    
    et = ElementTree.fromstring(castle_as_string)
    rooms = et.findall('room')
    
    for room in rooms:
        # Get id
        id = room.attrib['id']
        
        # Get message 
        message = room.find('message').text.strip()
        
        # Add exits to dict if we got 'em
        exits_et = room.find('exits')
        exits = {}
        if exits_et:
            exits = {}
            
            for exit_el in exits_et.getchildren():
                exits[exit_el.tag] = exit_el.text
            
            # Replace |EXITS| in message with a csv of exits
            exits_csv = ','.join(['"%s"' % (x) for x in exits.keys()])
            message = message.replace("|EXITS|", exits_csv)
        
        room = DummyRoom(id, message, exits)
        
        dummy_castle.add_room(room)

print "Version Test"
current_room = dummy_castle.get_room_by_index(0)
current_room.print_message()

sys.exit()

collect_input = True
while collect_input:
    input = raw_input("")
    
    # Convert message
    response = current_room.message
    
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
    carried_item = False
    if "stuff" in response:
        for item in response['stuff']:
        
            # TODO: include artifact
            print item.keys()
            if ('frog' in item.keys()) and (input == '(carry (frog))'):
                print item
                carried_item = item
                break
            
            item_int_mapping = {
                'treasure' : 'value',
                'weapon' : 'lethality',
            }
            for item_key in item_int_mapping.keys():
                if item_key in item.keys():
                    if input == '(carry (%s "%s" %i))' % \
                                        (item_key,
                                         item[item_key],
                                         item[item_int_mapping[item_key]]):
                        
                        carried_item = item
                        break
            
            if carried_item:
                break
        
        if carried_item:
            # Delete item from room
            response['stuff'].remove(carried_item)
            
            # Update message with item taken away
            current_room.set_message(response)
            current_room.print_message()
            continue
    
    
    
    