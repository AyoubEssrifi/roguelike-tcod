import tcod as libtcod
from enum import Enum

from game_states import GameStates
from menus import inventory_menu, level_up_menu, character_screen

INVENTORY_WIDTH = 50

class RenderOrder(Enum):
    STAIRS = 1
    CORPSE = 2
    ITEM = 3
    ACTOR = 4

def get_names_on_mouse_hover(mouse, game_map, fov_map):
    (x, y) = (mouse.cx, mouse.cy)
    
    if libtcod.map_is_in_fov(fov_map, x, y):
        entities_in_tile = game_map.get_entities(x, y)
        for entity in entities_in_tile:
            name = entity.name
            return name 
    
    return ''
    
def render_bar(panel, x, y, total_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * total_width)
    
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
    
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
    
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, int(x + total_width / 2), y, libtcod.BKGND_NONE, libtcod.CENTER,
                             '{0}: {1}/{2}'.format(name, value, maximum))
    
def render_all(con, panel, entities, player, screen_width, screen_height, game_map, fov_map, fov_recompute,
               message_log, bar_width, panel_height, panel_y, mouse, colors, game_state):
    # Draw all tiles
    if fov_recompute:
        for y in range(game_map.height):
            for x in range(game_map.width):
                wall = game_map.tiles[x][y].block_sight
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                explored = game_map.tiles[x][y].explored
                
                if visible:
                    game_map.tiles[x][y].explored = True
                    
                    if wall:
                        libtcod.console_set_char_background(con, x, y, colors.get('light_wall'), libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, colors.get('light_ground'), libtcod.BKGND_SET)
                elif explored:
                    if wall:
                        libtcod.console_set_char_background(con, x, y, colors.get('dark_wall'), libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, colors.get('dark_ground'), libtcod.BKGND_SET)
                    
    # Draw all entities
    entities_in_render_order = sorted(entities, key=lambda x: x.render_order.value)
    for entity in entities_in_render_order:
        draw_entity(con, fov_map, entity, game_map)
        
    libtcod.console_blit(con, 0, 0, screen_width, screen_height, 0, 0, 0)    
    
    # Display panel with bars and message log
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
    
    # Display message log
    y = 1
    for message in message_log.messages:
        libtcod.console_set_default_foreground(panel, message.color)
        libtcod.console_print_ex(panel, message_log.x, y, libtcod.BKGND_NONE, libtcod.LEFT, message.text)
        y += 1
    
    # Display health bar
    render_bar(panel, 1, 1, bar_width, 'HP', player.fighter.hp, player.fighter.max_hp,
               libtcod.green, libtcod.darker_red)
    
    # Display XP bar
    render_bar(panel, 1, 3, bar_width, 'XP', player.level.current_xp, player.level.experience_to_next_level,
               libtcod.light_blue, libtcod.dark_blue)
    
    # Display dungeon level
    libtcod.console_print_ex(panel, 1, 5, libtcod.BKGND_NONE, libtcod.LEFT, 
                             'Dungeon Level {0}'.format(game_map.dungeon_level))
    
    # Display names on mouse hover
    libtcod.console_set_default_foreground(panel, libtcod.gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_on_mouse_hover(mouse, game_map, fov_map))
    
    libtcod.console_blit(panel, 0, 0, screen_width, panel_height, 0, 0, panel_y)
    
    # Display inventory menu
    if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        if game_state == GameStates.SHOW_INVENTORY:
            inventory_title = 'Press the key next to an item to use it, or Esc to cancel.\n'
        else:
            inventory_title = 'Press the key next to an item to drop it, or Esc to cancel.\n'
            
        inventory_menu(con, inventory_title, player.inventory, INVENTORY_WIDTH, screen_width, screen_height)
    
    # Display level up menu
    elif game_state == GameStates.LEVEL_UP:
        level_up_menu(con, 'Level up! Choose a stat to raise:', player, 40, screen_width, screen_height)
    
    # Display character screen menu
    elif game_state == GameStates.CHARACTER_SCREEN:
        character_screen(player, 30, 10, screen_width, screen_height)
    
def clear_all(con, entities):
    # Clear all entities
    for entity in entities:
        clear_entity(con, entity)
    
def draw_entity(con, fov_map, entity, game_map):
    if libtcod.map_is_in_fov(fov_map, entity.x, entity.y) or (entity.stairs and game_map.tiles[entity.x][entity.y].explored):
        libtcod.console_set_default_foreground(con, entity.color)
        libtcod.console_put_char(con, entity.x, entity.y, entity.char, libtcod.BKGND_NONE)
        
def clear_entity(con, entity):
    libtcod.console_put_char(con, entity.x, entity.y, ' ', libtcod.BKGND_NONE)