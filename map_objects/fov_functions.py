import tcod as libtcod

from map_objects.game_map import GameMap

def initialize_fov(game_map: GameMap) -> libtcod.map.Map:
    fov_map = libtcod.map.Map(game_map.width, game_map.height)
    
    for y in range(game_map.height):
        for x in range(game_map.width):
            fov_map.transparent[y][x] = not game_map.tiles[x][y].block_sight
            fov_map.walkable[y][x] = not game_map.tiles[x][y].blocked
    
    return fov_map
            
def recompute_fov(fov_map, x, y, fov_algorithm=0, fov_radius=5, fov_light_walls=True):
    libtcod.map_compute_fov(fov_map, x, y, fov_radius, fov_light_walls, fov_algorithm)