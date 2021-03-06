import tcod as libtcod
import os
import sys

from loader_functions.initialize_new_game import get_constants, get_game_variables
from loader_functions.data_loaders import save_game, load_game
from input_handler import handle_keys, handle_mouse, handle_main_menu
from render_functions import render_all, clear_all
from map_objects.fov_functions import initialize_fov, recompute_fov
from game_states import GameStates
from death_functions import kill_monster, kill_player
from game_messages import Message
from menus import main_menu, message_box


def main():
    # Initializing game
    constants = get_constants()
    
    font_file = os.getcwd() + '/resources/arial10x10.png'
    
    # Console init
    libtcod.console_set_custom_font(font_file, libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    root_con = libtcod.console_init_root(constants['screen_width'], constants['screen_height'], constants['window_title'], False)
    con = libtcod.console_new(constants['screen_width'], constants['screen_height'])
    panel = libtcod.console_new(constants['screen_width'], constants['panel_height'])
    
    player = None
    entities = []
    game_map = None
    message_log = None
    game_state = None
    
    show_main_menu = True
    show_load_error_message = False
    
    main_menu_background_image = None
    
    key = libtcod.Key()
    mouse = libtcod.Mouse()
    
    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        
        if show_main_menu:
            main_menu(con, constants['screen_width'], constants['screen_height'])
            
            if show_load_error_message:
                message_box(con, 'No save game to load.', 50, constants['screen_width'], constants['screen_height'])
            
            libtcod.console_flush()
            
            action = handle_main_menu(key)
            
            new_game = action.get('new_game')
            load_saved_game = action.get('load_game')
            exit_game = action.get('exit_game')
            
            if show_load_error_message and (new_game or load_saved_game or exit_game):
                show_load_error_message = False
                root_con.clear()
                
            elif new_game:
                player, entities, game_map, message_log, game_state = get_game_variables(constants)
                
                show_main_menu = False
                
            elif load_saved_game:
                try:
                    player, entities, game_map, message_log, game_state = load_game()
                
                    show_main_menu = False
                except FileNotFoundError:
                    show_load_error_message = True
                    
            elif exit_game:
                break
        else:
            libtcod.console_clear(con)
            play_game(player, entities, game_map, message_log, game_state, con, panel, constants)
            
            show_main_menu = True
            
def play_game(player, entities, game_map, message_log, game_state, con, panel, constants):
    # FOV init
    fov_recompute = True
    fov_map = initialize_fov(game_map)
    
    # Game State
    previous_game_state = game_state
    
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
        wait = action.get("wait")
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        drop_inventory = action.get('drop_inventory')
        inventory_index = action.get("inventory_index")
        take_stairs = action.get("take_stairs")
        level_up_stat = action.get("level_up_stat")
        show_character_screen = action.get("show_character_screen")
        fullscreen = action.get("fullscreen")
        exit_game = action.get("exit")
        
        left_click = mouse_action.get('left_click')
        right_click = mouse_action.get('right_click')
        
        # Managing player's turn 
        player_turn_results = []
        
        # Handling player waiting
        if wait:
            game_state = GameStates.ENEMY_TURN
            
        # Handling player movement and fighting
        elif move and game_state == GameStates.PLAYERS_TURN:
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
            
        # Handling targeting
        if game_state == GameStates.TARGETING:
            if left_click:
                target_x, target_y = left_click
                item_use_results = player.inventory.use(targeting_item, entities=entities, fov_map=fov_map, target_x=target_x, target_y=target_y)
                player_turn_results.extend(item_use_results)
            elif right_click:
                player_turn_results.append({'targeting_cancelled': True})    
        
        # Handling stairs
        if take_stairs and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.stairs and entity.x == player.x and entity.y == player.y:
                    entities = game_map.next_floor(player, constants, message_log)
                    fov_map = initialize_fov(game_map)
                    fov_recompute = True
                    libtcod.console_clear(con)
                    break
            else:
                message_log.add_message(Message('There are no stairs here.', libtcod.yellow))
        
        # Handling stats increase when leveling up         
        if level_up_stat:
            if level_up_stat == "hp":
                player.fighter.base_max_hp += 20
                player.fighter.hp = player.fighter.max_hp
            elif level_up_stat == "str":
                player.fighter.base_power += 1
            elif level_up_stat == "def":
                player.fighter.base_defense += 1
                
            game_state = previous_game_state
        
        # Handling character screen
        if show_character_screen:
            previous_game_state = game_state
            game_state = GameStates.CHARACTER_SCREEN
    
        # Handling player turn results
        for result in player_turn_results:
            message = result.get('message')
            dead_entity = result.get('dead')
            xp = result.get('xp')
            item_added = result.get('item_added')
            item_consumed = result.get("consumed")
            item_dropped = result.get("item_dropped")
            equip = result.get("equip")
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
            
            if xp:
                leveled_up = player.level.add_xp(xp)
                if leveled_up:
                    message_log.add_message(Message(
                        'Your battle skills grow stronger! You reached level {0}'.format(
                        player.level.current_level) + '!', libtcod.yellow))
                    
                    previous_game_state = game_state
                    game_state = GameStates.LEVEL_UP
                
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
            
            if equip:
                equip_results = player.equipement.toggle_equip(equip)
                
                for equip_result in equip_results:
                    equipped = equip_result.get("equipped")
                    dequipped = equip_result.get("dequipped")
                    
                    if equipped:
                        message_log.add_message(Message('You equipped the {0}'.format(equipped.name)))

                    if dequipped:
                        message_log.add_message(Message('You dequipped the {0}'.format(dequipped.name)))
                
                game_state = GameStates.ENEMY_TURN
            
            if targeting:
                # We???re setting the game state to the player???s turn rather than the actual previous state.
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
            if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY, GameStates.CHARACTER_SCREEN):
                game_state = previous_game_state
            elif game_state == GameStates.TARGETING:
                player_turn_results.append({'targeting_cancelled': True})
            else:
                save_game(player, entities, game_map, message_log, game_state)
                # libtcod.console_clear(con)
                return True


if __name__ == "__main__":
    main()