import tcod as libtcod

from game_messages import Message

class Inventory:
    def __init__(self, capacity):
        self.capacity = 26
        self.items = []
    
    def add_item(self, item):
        results = []
        
        if len(self.items) >= self.capacity:
            results.append({'item_added': None, 
                            'message': Message('You cannot carry anymore !', libtcod.yellow)})
        
        else:
            results.append({'item_added': item, 
                            'message': Message('You pick up the {0}'.format(item.name), libtcod.yellow)})
            
            self.items.append(item)
        
        return results