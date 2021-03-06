from __future__ import annotations
import tcod as libtcod
from random import randint


from map_objects.tile import Tile
from map_objects.rectangle import Rect
from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster
from components.item import Item
from components.stairs import Stairs
from components.equippable import Equippable
from equipement_slots import EquipementSlots
from render_functions import RenderOrder
from item_functions import heal, cast_lightning, cast_fireball, cast_confuse
from game_messages import Message
from random_utils import random_choice_from_dict, from_dungeon_level


class GameMap:
    def __init__(self, width, height, dungeon_level=1):
        self.width = width
        self.height = height
        self.dungeon_level = dungeon_level
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
                
    def make_map(self, room_min_size, room_max_size, max_rooms,
                 map_width, map_height, player, entities):
        rooms = []
        num_rooms = 0
        
        center_of_last_room_x = None
        center_of_last_room_y = None
        
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
                
                center_of_last_room_x = new_x
                center_of_last_room_y = new_y

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
                
                self.place_entities(entities, new_room)
                rooms.append(new_room)
                num_rooms += 1   
                
        # Placing the stairs to next level
        stairs_component = Stairs(self.dungeon_level + 1)
        stairs = Entity(center_of_last_room_x, center_of_last_room_y, 'Stairs', '>', libtcod.white,
                        stairs=stairs_component, render_order=RenderOrder.STAIRS)
        entities.append(stairs)  
    
    def place_entities(self, entities: List, room: Rect):
        max_monsters_per_room = from_dungeon_level([[2, 1], [3, 4], [5, 6]], self.dungeon_level)
        max_items_per_room = from_dungeon_level([[1, 1], [2, 4]], self.dungeon_level)
        
        monster_chances = {'orc': 80,
                           'troll': 20
                           }
        item_chances = {'sword': from_dungeon_level([[5, 4]], self.dungeon_level),
                        'shield': from_dungeon_level([[15, 8]], self.dungeon_level),
                        'healing_potion': 70,
                        'lightning_scroll': 10,
                        'fireball_scroll': 10,
                        'confusion_scroll': 10,
                        }
        
        # Placing random monsters
        for i in range(max_monsters_per_room):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            if len(self.get_entities(x, y)) == 0:
                monster_choice = random_choice_from_dict(monster_chances)
                # Probability of 80% to spawn Orc and 20% for Troll
                if monster_choice == 'orc':
                    fighter_component = Fighter(hp=10, defense=0, power=4, xp=35)
                    ai_component = BasicMonster()
                    monster = Entity(x, y, "Orc", "o", libtcod.dark_green, fighter_component, ai_component, render_order=RenderOrder.ACTOR)
                else:
                    fighter_component = Fighter(hp=16, defense=1, power=8, xp=100)
                    ai_component = BasicMonster()
                    monster = Entity(x, y, "Troll", "T", libtcod.orange, fighter_component, ai_component, render_order=RenderOrder.ACTOR)
                
                # Add the monster as an entity property of the tile to check for blocking movement
                # self.tiles[x][y].entity = monster
                self.set_entity(x, y, monster)
                
                entities.append(monster)
        
        # Placing random items
        for i in range(max_items_per_room):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            if len(self.get_entities(x, y)) == 0:
                item_choice = random_choice_from_dict(item_chances)
                
                if item_choice == 'sword':
                    equippable_component = Equippable(EquipementSlots.MAIN_HAND, power_bonus=3)
                    item = Entity(x, y, 'Sword', '-', libtcod.sky, equippable=equippable_component)
                elif item_choice == 'shield':
                    equippable_component = Equippable(EquipementSlots.OFF_HAND, defense_bonus=1)
                    item = Entity(x, y, 'Shield', ']', libtcod.darker_orange, equippable=equippable_component)
                elif item_choice == 'healing_potion':
                    item_component = Item(use_function=heal, amount=40)
                    item = Entity(x, y, 'Healing Potion', '!', libtcod.violet, item=item_component, render_order=RenderOrder.ITEM)
                elif item_choice == 'fireball_scroll':
                    item_component = Item(use_function=cast_fireball, targeting=True, targeting_message=Message(
                        'Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan), damage=25, radius=3)
                    item = Entity(x, y, 'Fireball Scroll', '#', libtcod.red, item=item_component, render_order=RenderOrder.ITEM)
                elif item_choice == 'confusion_scroll':
                    item_component = Item(use_function=cast_confuse, targeting=True, targeting_message=Message(
                        'Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan), radius=3)
                    item = Entity(x, y, 'Confusion Scroll', '#', libtcod.light_pink, item=item_component, render_order=RenderOrder.ITEM)
                else:
                    item_component = Item(use_function=cast_lightning, damage=40, maximum_range=5)
                    item = Entity(x, y, 'Lightning Scroll', '#', libtcod.yellow, item=item_component, render_order=RenderOrder.ITEM)
                    
                # Add item as an entity property of the tile
                self.set_entity(x, y, item)
                
                entities.append(item)
    
    def next_floor(self, player, constants, message_log):
        self.dungeon_level += 1
        entities = [player]
        
        self.tiles = self.initialize_tiles()
        self.make_map(constants['room_min_size'], constants['room_max_size'], constants['max_rooms'],
                      constants['map_width'], constants['map_height'], player, entities)
        
        player.fighter.heal(player.fighter.max_hp // 2)
        
        message_log.add_message(Message('You take a moment to rest, and recover your strength.', libtcod.light_violet))
        
        return entities