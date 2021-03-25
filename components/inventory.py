from __future__ import annotations
import tcod as libtcod

from game_messages import Message

class Inventory:
    def __init__(self, capacity):
        self.capacity = 26
        self.items = []
    
    def add_item(self, item: Entity):
        results = []
        
        if len(self.items) >= self.capacity:
            results.append({'item_added': None, 
                            'message': Message('You cannot carry anymore !', libtcod.yellow)})
        
        else:
            results.append({'item_added': item, 
                            'message': Message('You pick up the {0}'.format(item.name), libtcod.yellow)})
            
            self.items.append(item)
        
        return results
    
    def remove_item(self, item: Entity):
        self.items.remove(item)
        
    def use(self, item_entity: Entity, **kwargs):
        results = []
        
        item_component = item_entity.item
        
        if item_component.use_function:
            if item_component.targeting and not (kwargs.get('target_x') or kwargs.get('target_y')):
                results.append({'targeting': item_entity})
            else:
                # Merge the kwargs of the item component and kwargs of this function
                kwargs = {**item_component.function_kwargs, **kwargs}
                
                item_use_results = item_component.use_function(self.owner, **kwargs)
                
                for item_use_result in item_use_results:
                    if item_use_result.get('consumed'):
                        self.remove_item(item_entity)
                
                results.extend(item_use_results)
            
        else:
            results.append({'message': Message('The {0} cannot be used.'.format(item_entity.name))})
        
        return results
    
    def drop_item(self, item: Entity):
        results = []
        
        item.x = self.owner.x
        item.y = self.owner.y
        
        self.remove_item(item)
        results.append({'item_dropped': item, 
                        'message': Message('You dropped the {0}'.format(item.name), libtcod.yellow)})
        
        return results