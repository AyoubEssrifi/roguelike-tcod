from __future__ import annotations
import tcod as libtcod
from random import randint


from map_objects.tile import Tile
from map_objects.rectangle import Rect
from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster
from components.item import Item
from render_functions import RenderOrder



class GameMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = self.initialize_tiles()

    def initialize_tiles(self):
        tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]

        return tiles
    
    def is_blocked(self, x, y):
        if self.tiles[x][y].blocked:
            return True
        return False
    
    def get_entities(self, x, y):
        return self.tiles[x][y].entities
        
    def set_entity(self, x, y, entity):
        self.tiles[x][y].entities.append(entity)
        
    def remove_entity(self, x, y, entity):
        self.tiles[x][y].entities.remove(entity)
    
    def create_room(self, room: Rect):
        # Go through the tiles in the rectangle and make them passable
        for y in range(room.y1 + 1, room.y2):
            for x in range(room.x1 + 1, room.x2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False
    
    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
    
    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
                
    def make_map(self, room_min_size, room_max_size, max_rooms, max_monsters_per_room, max_items_per_room, 
                 map_width, map_height, player, entities):
        rooms = []
        num_rooms = 0
        
        for r in range(max_rooms):
            w = randint(room_min_size, room_max_size)
            h = randint(room_min_size, room_max_size)
            x = randint(0, map_width - w - 1)
            y = randint(0, map_height - h - 1)
            new_room = Rect(x, y, w , h)
            
            # Run through the other rooms and see if they intersect with this one
            for other_room in rooms:
                if new_room.intersect(other_room):
                    break 
            else:
                self.create_room(new_room)
                
                # Center coordinates of new room, will be useful later
                (new_x, new_y) = new_room.center()

                if num_rooms == 0:
                    # This is the first room, where the player starts at
                    player.x = new_x
                    player.y = new_y
                    
                    # Add player to tile entities
                    self.set_entity(player.x, player.y, player)
                else:
                    # all rooms after the first:
                    # connect it to the previous room with a tunnel
                    (prev_x, prev_y) = rooms[-1].center()
                    
                    # flip a coin (random number that is either 0 or 1)
                    if randint(0, 1) == 1:
                        # first move horizontally, then vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        # first move vertically, then horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)
                
                self.place_entities(entities, new_room, max_monsters_per_room, max_items_per_room)
                rooms.append(new_room)
                num_rooms += 1     
    
    def place_entities(self, entities: List, room: Rect, max_monsters_per_room, max_items_per_room):
        number_of_monsters = randint(1, max_monsters_per_room)
        number_of_items = randint(1, max_items_per_room)
        
        # Placing random monsters
        for i in range(number_of_monsters):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            if len(self.get_entities(x, y)) == 0:
                # Probability of 80% to spawn Orc and 20% for Troll
                if randint(0, 100) < 80:
                    fighter_component = Fighter(hp=10, defense=0, power=3)
                    ai_component = BasicMonster()
                    monster = Entity(x, y, "Orc", "o", libtcod.dark_green, fighter_component, ai_component, render_order=RenderOrder.ACTOR)
                else:
                    fighter_component = Fighter(hp=16, defense=1, power=4)
                    ai_component = BasicMonster()
                    monster = Entity(x, y, "Troll", "T", libtcod.orange, fighter_component, ai_component, render_order=RenderOrder.ACTOR)
                
                # Add the monster as an entity property of the tile to check for blocking movement
                # self.tiles[x][y].entity = monster
                self.set_entity(x, y, monster)
                
                entities.append(monster)
        
        # Placing random items
        for i in range(number_of_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            if len(self.get_entities(x, y)) == 0:
                item_component = Item()
                item = Entity(x, y, 'Healing Potion', '!', libtcod.violet, item=item_component, render_order=RenderOrder.ITEM)
                
                # Add item as an entity property of the tile
                self.set_entity(x, y, item)
                
                entities.append(item)