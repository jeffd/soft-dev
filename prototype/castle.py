# Data structures for game player

class Location:
    def __init__(self, floor, x, y):
        self.location = (floor, x, y)
    
    def __repr__(self):
        return str(self.location)
    
    def get_location(self):
        return self.location
    
    def next_location(self, direction):
        """ Returns the next location that will we be in given that
        we go 'direction' (String) """
        # <direction>  ::=  up  |  down  |  east  |  west  |  north  |  south
        return {
            'up': lambda x: Location(x[0]+1, x[1], x[2]),
            'down' : lambda x: Location(x[0]-1, x[1], x[2]),
            'east' : lambda x: Location(x[0], x[1]-1, x[2]),
            'west' : lambda x: Location(x[0], x[1]+1, x[2]),
            'north' : lambda x: Location(x[0], x[1], x[2]+1),
            'south' : lambda x: Location(x[0], x[1], x[2]-1),
        }[direction](self.location)

class Castle:
    
    def __init__(self):
        self.visited_locations = []
        self.exits = []
    
    def add_visited_location(self, location):
        self.visited_locations.append(location)
    
    def get_visited_locations(self, location):
        return self.visited_locations
    
    def visited_location(self, location):
        return location in self.visited_locations
    
    def add_exit(self, location):
        self.exits.append(location)
    
    def get_exits(self, location):
        return self.exits



