import tcod as libtcod
import os
import sys

from loader_functions.initialize_new_game import get_constants, get_game_variables
from input_handler import handle_keys, handle_mouse
from render_functions import render_all, clear_all
from map_objects.fov_functions import initialize_fov, recompute_fov
from game_states import GameStates
from death_functions import kill_monster, kill_player
from game_messages import Message

def main():
    # Initializing game
    constants = get_constants()
    player, entities, game_map, message_log, game_state = get_game_variables(constants)
    
    font_file = os.getcwd() + '/resources/arial10x10.png'
    
    # FOV init
    fov_recompute = True
    fov_map = initialize_fov(game_map)
    
    # Game State
    previous_game_state = game_state
    
    # Console init
    libtcod.console_set_custom_font(font_file, libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    root_con = libtcod.console_init_root(constants['screen_width'], constants['screen_height'], constants['window_title'], False)
    con = libtcod.console_new(constants['screen_width'], constants['screen_height'])
    panel = libtcod.console_new(constants['screen_width'], constants['panel_height'])
    
    # Keyboard + Mouse vars
    key = libtcod.Key()
    mouse = libtcod.Mouse()
    
    # Targeting system
    targeting_item = None
    
    # Game Loop
    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        
        # Rendering
        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, constants['fov_algorithm'], 
                          constants['fov_radius'], constants['fov_light_walls'])
            
        render_all(con, panel, entities, player, constants['screen_width'], constants['screen_height'],
                   game_map, fov_map, fov_recompute, message_log, constants['bar_width'], 
                   constants['panel_height'], constants['panel_y'], mouse, constants['colors'], game_state)
        
        fov_recompute = False
        libtcod.console_flush()
        clear_all(con, entities)

        action = handle_keys(key, game_state)
        mouse_action = handle_mouse(mouse)
        
        move = action.get("move")
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        drop_inventory = action.get('drop_inventory')
        inventory_index = action.get("inventory_index")
        fullscreen = action.get("fullscreen")
        exit_game = action.get("exit")
        
        left_click = mouse_action.get('left_click')
        right_click = mouse_action.get('right_click')
        
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
        
        # Handling targeting
        if game_state == GameStates.TARGETING:
            if left_click:
                target_x, target_y = left_click
                item_use_results = player.inventory.use(targeting_item, entities=entities, fov_map=fov_map, target_x=target_x, target_y=target_y)
                player_turn_results.extend(item_use_results)
            elif right_click:
                player_turn_results.append({'targeting_cancelled': True})
        
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
            targeting = result.get("targeting")
            targeting_cancelled = result.get("targeting_cancelled")
            
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
            
            if targeting:
                # We’re setting the game state to the player’s turn rather than the actual previous state.
                # This is so that cancelling the targeting will not reopen the inventory screen.
                previous_game_state = GameStates.PLAYERS_TURN
                game_state = GameStates.TARGETING
                
                targeting_item = targeting
                
                message_log.add_message(targeting.item.targeting_message)
            
            if targeting_cancelled:
                game_state = previous_game_state
                message_log.add_message(Message('Targeting cancelled.'))
            
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
            elif game_state == GameStates.TARGETING:
                player_turn_results.append({'targeting_cancelled': True})
            else:
                return True


if __name__ == "__main__":
    main()