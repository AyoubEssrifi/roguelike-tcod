import tcod as libtcod

from entity import Entity
from map_objects.game_map import GameMap
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from render_functions import RenderOrder
from game_messages import MessageLog
from game_states import GameStates


def get_constants():
    # Window config
    window_title = 'Roguelike Tutorial'
    screen_width = 100
    screen_height = 50
    
    # UI config
    # Bars config
    bar_width = 20
    panel_height = 7
    panel_y = screen_height - panel_height
    
    # Message Log config
    message_x = bar_width + 2
    message_width = screen_width - bar_width - 2
    message_height = panel_height - 1
    
    # Map config
    map_width = 80
    map_height = 45
    
    room_max_size = 10
    room_min_size = 6
    max_rooms = 30
    max_monsters_per_room = 3
    max_items_per_room = 5
    
    # FOV config
    fov_algorithm = 0
    fov_radius = 8
    fov_light_walls = True
    
    # Colors config
    colors = {
        'dark_wall': libtcod.Color(0, 0, 100),
        'dark_ground': libtcod.Color(50, 50, 150),
        'light_wall': libtcod.Color(130, 110, 50),
        'light_ground': libtcod.Color(200, 180, 50)
    }
    
    constants = {
        'window_title': window_title,
        'screen_width': screen_width,
        'screen_height': screen_height,
        'bar_width': bar_width,
        'panel_height': panel_height,
        'panel_y': panel_y,
        'message_x': message_x,
        'message_width': message_width,
        'message_height': message_height,
        'map_width': map_width,
        'map_height': map_height,
        'room_max_size': room_max_size,
        'room_min_size': room_min_size,
        'max_rooms': max_rooms,
        'fov_algorithm': fov_algorithm,
        'fov_light_walls': fov_light_walls,
        'fov_radius': fov_radius,
        'colors': colors
    }
    
    return constants

def get_game_variables(constants):
    # Components
    fighter_component = Fighter(hp=100, defense=2, power=5)
    inventory_component = Inventory(26)
    level_component = Level()
    
    # Entities
    player = Entity(int(constants['screen_width'] / 2) - 10, int(constants['screen_height'] / 2), "Player", "@", libtcod.white, 
                    fighter=fighter_component, ai=None, inventory=inventory_component, level=level_component,
                    render_order=RenderOrder.ACTOR)
    entities = [player]
    
    game_map = GameMap(constants['map_width'], constants['map_height'])
    game_map.make_map(constants['room_min_size'], constants['room_max_size'], constants['max_rooms'],
                      constants['map_width'], constants['map_height'], player, entities)
    
    # Message Log init
    message_log = MessageLog(constants['message_x'], constants['message_width'], constants['message_height'])
    
    # Game State
    game_state = GameStates.PLAYERS_TURN
    
    return player, entities, game_map, message_log, game_state