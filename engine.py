import tcod as libtcod
import os
import sys

from input_handler import handle_keys
from entity import Entity
from render_functions import render_all, clear_all, RenderOrder
from map_objects.game_map import GameMap
from map_objects.fov_functions import initialize_fov, recompute_fov
from game_states import GameStates
from components.fighter import Fighter
from components.inventory import Inventory
from death_functions import kill_monster, kill_player
from game_messages import MessageLog, Message

def main():
    font_file = os.getcwd() + '/resources/arial10x10.png'
    
    # Window config
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
    
    # Components
    fighter_component = Fighter(hp=30, defense=2, power=5)
    inventory_component = Inventory(26)
    
    # Entities
    player = Entity(int(screen_width / 2) - 10, int(screen_height / 2), "Player", "@", libtcod.white, 
                    fighter=fighter_component, ai=None, inventory=inventory_component, render_order=RenderOrder.ACTOR)
    entities = [player]
    
    # Map config
    map_width = 80
    map_height = 45
    
    room_max_size = 10
    room_min_size = 6
    max_rooms = 30
    max_monsters_per_room = 3
    max_items_per_room = 2
    
    game_map = GameMap(map_width, map_height)
    game_map.make_map(room_min_size, room_max_size, max_rooms, max_monsters_per_room, max_items_per_room, 
                      map_width, map_height, player, entities)
    
    # FOV config
    fov_algorithm = 0
    fov_radius = 8
    fov_light_walls = True
    fov_recompute = True
    
    fov_map = initialize_fov(game_map)
    
    # Colors config
    colors = {
        'dark_wall': libtcod.Color(0, 0, 100),
        'dark_ground': libtcod.Color(50, 50, 150),
        'light_wall': libtcod.Color(130, 110, 50),
        'light_ground': libtcod.Color(200, 180, 50)
    }
    
    # Game State
    game_state = GameStates.PLAYERS_TURN
    previous_game_state = game_state
    
    # Console init
    libtcod.console_set_custom_font(font_file, libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    root_con = libtcod.console_init_root(screen_width, screen_height, "Roguelike Dev", False)
    con = libtcod.console_new(screen_width, screen_height)
    panel = libtcod.console_new(screen_width, panel_height)
    
    # Message Log init
    message_log = MessageLog(message_x, message_width, message_height)
    
    # Keyboard + Mouse vars
    key = libtcod.Key()
    mouse = libtcod.Mouse()
    
    # Game Loop
    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        
        # Rendering
        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, fov_algorithm, fov_radius, fov_light_walls)
            
        render_all(con, panel, entities, player, screen_width, screen_height, game_map, fov_map, fov_recompute,
                   message_log, bar_width, panel_height, panel_y, mouse, colors, game_state)
        
        fov_recompute = False
        libtcod.console_flush()
        clear_all(con, entities)

        action = handle_keys(key, game_state)
        move = action.get("move")
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        drop_inventory = action.get('drop_inventory')
        inventory_index = action.get("inventory_index")
        fullscreen = action.get("fullscreen")
        exit_game = action.get("exit")
        
        # Managing player's turn 
        player_turn_results = []
        
        # Handling player movement and fighting
        if move and game_state == GameStates.PLAYERS_TURN:
            dx, dy = move
            if not game_map.is_blocked(player.x + dx, player.y + dy):
                entities_in_tile = game_map.get_entities(player.x + dx, player.y + dy)
                if not any(entity.fighter for entity in entities_in_tile):
                    player.move(dx, dy, game_map)
                    fov_recompute = True
                else:
                    for entity in entities_in_tile:
                        if entity.fighter:
                            target = entity
                            
                    # Avoid attacking items xD
                    if not target.item:
                        player_attack_results = player.fighter.attack(target)
                        player_turn_results.extend(player_attack_results)
                
                game_state = GameStates.ENEMY_TURN
        
        # Handling picking up items
        elif pickup and game_state == GameStates.PLAYERS_TURN:
            entities_in_tile = game_map.get_entities(player.x, player.y)
            picked = False
            for entity in entities_in_tile:
                if entity.item:
                    item = entity
                    pickup_results = player.inventory.add_item(item)
                    player_turn_results.extend(pickup_results)
                    picked = True
                    break
            if not picked:
                message_log.add_message(Message('There is nothing to pick up here !', libtcod.yellow))
                
            
        # Handling inventory
        if show_inventory:
            previous_game_state = game_state
            game_state = GameStates.SHOW_INVENTORY
            
        if inventory_index is not None and previous_game_state != GameStates.PLAYER_DEAD and inventory_index < len(player.inventory.items):
            item = player.inventory.items[inventory_index]
            if game_state == GameStates.SHOW_INVENTORY:
                player_turn_results.extend(player.inventory.use(item, entities=entities, fov_map=fov_map))
            elif game_state == GameStates.DROP_INVENTORY:
                player_turn_results.extend(player.inventory.drop_item(item))
        
        if drop_inventory:
            previous_game_state = game_state
            game_state = GameStates.DROP_INVENTORY
            
        # Handling player turn results
        for result in player_turn_results:
            message = result.get('message')
            dead_entity = result.get('dead')
            item_added = result.get('item_added')
            item_consumed = result.get("consumed")
            item_dropped = result.get("item_dropped")
            
            if message:
                message_log.add_message(message)
                
            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity)
                else:
                    message = kill_monster(dead_entity, game_map)
                    
                message_log.add_message(message)
            
            if item_added:
                entities.remove(item_added)
                game_map.remove_entity(item_added.x, item_added.y, item_added)
                
                game_state = GameStates.ENEMY_TURN
            
            if item_consumed:
                game_state = GameStates.ENEMY_TURN
                
            if item_dropped:
                entities.append(item_dropped)
                game_map.set_entity(item_dropped.x, item_dropped.y ,item_dropped)
                game_state = GameStates.ENEMY_TURN
                
            
        # Managing enemy's turn
        if game_state == GameStates.ENEMY_TURN:
            for entity in entities:
                if entity.ai:
                    enemy_turn_results = []
                    enemy_attack_results = entity.ai.take_turn(player, entities, fov_map, game_map)
                    enemy_turn_results.extend(enemy_attack_results)
                    
                    for result in enemy_turn_results:
                        message = result.get('message')
                        dead_entity = result.get('dead')
                        
                        if message:
                            message_log.add_message(message)
                            
                        if dead_entity:
                            if dead_entity == player:
                                message, game_state = kill_player(dead_entity)
                            else:
                                message = kill_monster(dead_entity, game_map)
                            
                            message_log.add_message(message)
                            
                            if game_state == GameStates.PLAYER_DEAD:
                                break
                            
                    if game_state == GameStates.PLAYER_DEAD:
                        break
            else:     
                game_state = GameStates.PLAYERS_TURN
        
            
        if fullscreen:
            libtcod.console_set_fullscreen(fullscreen)
            
        if exit_game:
            if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
                game_state = previous_game_state
            else:
                return True


if __name__ == "__main__":
    main()