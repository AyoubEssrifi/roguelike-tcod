import tcod as libtcod

def handle_key(key):
    key_char = chr(key.c)
    
    # Movement keys
    if key.vk == libtcod.KEY_UP:
        return {"move": (0, -1)}
    elif key.vk == libtcod.KEY_DOWN:
        return {"move": (0, 1)}
    elif key.vk == libtcod.KEY_LEFT:
        return {"move": (-1, 0)}
    elif key.vk == libtcod.KEY_RIGHT:
        return {"move": (1, 0)}
    elif key.vk == libtcod.KEY_KP7:
        return {'move': (-1, -1)}
    elif key.vk == libtcod.KEY_KP9:
        return {'move': (1, -1)}
    elif key.vk == libtcod.KEY_KP1:
        return {'move': (-1, 1)}
    elif key.vk == libtcod.KEY_KP3:
        return {'move': (1, 1)}
    
    # Pickup item
    if key_char == 'g':
        return {'pickup': True}
    
    # Toggle fulscreen: Alt + Enter
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        return {"fullscreen": True}
    
    # Exit game
    if key.vk == libtcod.KEY_ESCAPE:
        return {"exit": True}
    
    # Nothing is pressed
    return {}