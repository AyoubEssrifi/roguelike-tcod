from __future__ import annotations
import tcod as libtcod

from game_states import GameStates
from render_functions import RenderOrder
from game_messages import Message

def kill_player(player: Entity):
    player.char = '%'
    player.color = libtcod.red
    
    return Message('You died !!', libtcod.red), GameStates.PLAYER_DEAD

def kill_monster(monster: Entity, game_map: GameMap):
    death_message = Message('{0} is dead!'.format(monster.name.capitalize()), libtcod.orange)
    
    monster.char = '%'
    monster.color = libtcod.red
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of {0}'.format(monster.name)
    monster.render_order = RenderOrder.CORPSE
    
    return death_message