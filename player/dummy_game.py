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
from random import randint
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
        self.is_outside = False
        self.set_message(message)
        # exits is a dict exits["east"] = "A"
        self.exits = exits
        self.encoder = JSONEncoder(indent=4)
    
    def __repr__(self):
        return 'Room %s Exits %s' % (self.id, str(self.exits))
    
    def set_message(self, message):
        # Assign message
        self.message = message
        
        # Mark as outside if that's the case
        if ('location' in message) and (message['location'] == 'outside the castle'):
            self.is_outside = True
        
    def get_message(self):
        return self.message

    def print_message(self):
        print self.encoder.encode(self.message)

    def get_exit_room_id(self, direction):
        return self.exits[direction]
    
class DummyCastle():
    
    def __init__(self):
        self.list_of_rooms = []
        self.current_room = None
        self.previous_room = None

    def update_current_room(self, room):
        self.previous_room = self.current_room
        self.current_room = room
    
    def add_room(self, room):
        self.list_of_rooms.append(room)
    
    def find_room(self, room_id):
        for room in self.list_of_rooms:
            if room.id == room_id:
                return room
        return False
    
    def get_room_by_index(self, index):
        return self.list_of_rooms[index]
    
    def get_outside_exit_rooms(self):
        """ Returns a list of ids all rooms with exits to outside """
        list = []
        
        for room in self.list_of_rooms:
            # See if exits include outside
            for exit_direction in room.exits:
                exit = self.find_room(room.exits[exit_direction])
                if exit.is_outside:
                    list.append(room.id)
        
        return list

    def set_random_room_accessible_outside(self):
        """ Sets the current room to a random room that has an exit outside """
        possible_rooms = self.get_outside_exit_rooms()
        
        random_room_id = possible_rooms[(randint(0, len(possible_rooms) - 1))]
        random_room = self.find_room(random_room_id)
        
        self.update_current_room(random_room)
            

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
            
            for exit_el in exits_et.getchildren():
                exits[exit_el.tag] = exit_el.text
            
            # Replace |EXITS| in message with a csv of exits
            exits_csv = ','.join(['"%s"' % (x) for x in exits.keys()])
            message = message.replace("|EXITS|", exits_csv)
        
        room = DummyRoom(id, loads(message), exits)
        
        dummy_castle.add_room(room)

print "Version Test | Castle ", options.castle_file
dummy_castle.previous_room = None
dummy_castle.current_room = dummy_castle.get_room_by_index(0)

collect_input = True
while collect_input:
    
    # Get current message
    response = dummy_castle.current_room.get_message()
    
    # Print current message
    dummy_castle.current_room.print_message()
    
    # Get input
    input = raw_input("")
    
    # Break if sent (stop)
    if input == "(stop)":
        print "You said stop"
        break
 
    # Handle outside the castle responses
    if ("location" in response) and (response["location"] == "outside the castle"):
        
        # If they say (enter) put them in the previous room
        if input == "(enter)":
            dummy_castle.update_current_room(dummy_castle.previous_room)
            continue
        
        # If they say (enter-randomly) put them in a random room
        if input == "(enter-randomly)":
            dummy_castle.set_random_room_accessible_outside()
            continue
    
        
    # See if they are going to go to an exit
    if ("location" in response) and ("room" in response['location']) \
        and ("exits" in response["location"]["room"]):
        
        next_iter = False
        
        exits = response["location"]["room"]["exits"]
        for exit in exits:
            if input == ('(go %s)' % (exit)):
                new_location = dummy_castle.current_room.get_exit_room_id(exit)
                dummy_castle.update_current_room(dummy_castle.find_room(new_location))
                next_iter = True
                break

        if next_iter:
            continue

    # See if they want to pickup anything
    carried_item = False
    if "stuff" in response:
        for item in response['stuff']:
        
            # See if they're picking up a frog
            if ('frog' in item.keys()) and (input == '(carry (frog))'):
                carried_item = item
                break
            
            # See if they're picking up a treasure or a weapon
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
            
            # See if they're picking up an artifact
            if ('artifact' in item.keys()) and ('description' in item.keys()):
                artifact_name, artifact_description = item['artifact'], \
                                                      item['description']

                if input == '(carry (artifact %s %s))' \
                          % (artifact_name, ', '.join(artifact_description)):
                    carried_item = item
                    break
        
        if carried_item:
            # Delete item from room
            response['stuff'].remove(carried_item)
            
            # If there's no more stuff left, delete key
            if len(response['stuff']) == 0:
                del response['stuff']
            
            # Update message with item taken away
            dummy_castle.current_room.set_message(response)
            continue
    
    print '{ error : "Command %s didn\'t make sense here." } ' % (input)
    sys.exit()
    
    