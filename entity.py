from __future__ import annotations
import math
import tcod as libtcod

from render_functions import RenderOrder

class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """
    def __init__(self, x, y, name, char, color, fighter: Fighter = None, ai: BasicMonster = None, 
                 item: Item = None, inventory: Inventory = None, stairs: Stairs = None,
                 render_order: RenderOrder = RenderOrder.CORPSE):
        self.x = x
        self.y = y
        self.name = name
        self.char = char
        self.color = color
        self.fighter = fighter
        self.ai = ai
        self.item = item
        self.inventory = inventory
        self.stairs = stairs
        self.render_order = render_order
        
        if self.fighter:
            self.fighter.owner = self
        
        if self.ai:
            self.ai.owner = self
            
        if self.item:
            self.item.owner = self
            
        if self.inventory:
            self.inventory.owner = self
            
        if self.stairs:
            self.stairs.owner = self
        

    def move(self, dx, dy, game_map):
        # Update the tiles entity property
        game_map.remove_entity(self.x, self.y, self)
        
        # Move the entity by a given amount
        self.x += dx
        self.y += dy
        
        # Update the tiles entity property
        game_map.set_entity(self.x, self.y, self)
        
    def move_towards(self, target_x, target_y, game_map: GameMap):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        
        if not (game_map.is_blocked(self.x + dx, self.y + dy) or len(game_map.get_entities(self.x + dx, self.y + dy)) == 0):
            self.move(dx, dy, game_map)
            
    def move_astar(self, target: Entity, entities: list, game_map: GameMap):
        # Create a FOV map that has the dimensions of the map
        fov_map = libtcod.map_new(game_map.width, game_map.height)
        
        # Scan the current map each turn and set all the walls as unwalkable
        for y1 in range(game_map.height):
            for x1 in range(game_map.width):
                fov_map.transparent[y1][x1] = not game_map.tiles[x1][y1].block_sight
                fov_map.walkable[y1][x1] = not game_map.tiles[x1][y1].blocked
                
                # Scan all the tiles to see if there are objects that must be navigated around
                # Check also that the object isn't self or the target (so that the start and the end points are free)
                # The AI class handles the situation if self is next to the target so it will not use this A* function anyway
                entities_in_tile = game_map.get_entities(x1, y1)
                if len(entities_in_tile) != 0:
                    for entity in entities_in_tile:
                        if entity != target and entity != self:
                            fov_map.walkable[y1][x1] = False
        
        # Allocate a A* path
        # The 1.41 is the normal diagonal cost of moving, it can be set as 0.0 if diagonal moves are prohibited
        my_path = libtcod.path_new_using_map(fov_map, 1.41)
        
        # Compute the path between self's coordinates and the target's coordinates
        libtcod.path_compute(my_path, self.x, self.y, target.x, target.y)
        
        # Check if the path exists, and in this case, also the path is shorter than 25 tiles
        # The path size matters if you want the monster to use alternative longer paths (for example through other rooms) if for example the player is in a corridor
        # It makes sense to keep path size relatively low to keep the monsters from running around the map if there's an alternative path really far away
        if not libtcod.path_is_empty(my_path) and libtcod.path_size(my_path) < 25:
            # Find the next coordinates in the computed full path
            x, y = libtcod.path_walk(my_path, True)
            if x or y:
                # Set self's coordinates to the next path tile
                self.move(x - self.x, y - self.y, game_map)
        else:
            # Keep the old move function as a backup so that if there are no paths (for example another monster blocks a corridor)
            # it will still try to move towards the player (closer to the corridor opening)
            self.move_towards(target.x, target.y, game_map)

        # Delete the path to free memory
        libtcod.path_delete(my_path)        
        
    def distance_to(self, other: Entity):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
    
    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
            
        
