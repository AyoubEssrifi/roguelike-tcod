from __future__ import annotations
from game_messages import Message

class Fighter:
    
    def __init__(self, hp, defense, power, xp=0):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
    
    @property
    def max_hp(self):
        if self.owner and self.owner.equipement:
            bonus = self.owner.equipement.max_hp_bonus
        else:
            bonus = 0
        
        return self.base_max_hp + bonus

    @property
    def defense(self):
        if self.owner and self.owner.equipement:
            bonus = self.owner.equipement.defense_bonus
        else:
            bonus = 0
        
        return self.base_defense + bonus
    
    @property
    def power(self):
        if self.owner and self.owner.equipement:
            bonus = self.owner.equipement.power_bonus
        else:
            bonus = 0
        
        return self.base_power + bonus
        
    def take_damage(self, amount):
        results = []
        
        self.hp -= amount
        
        if self.hp <= 0:
            self.hp = 0
            results.append({'dead': self.owner, 'xp': self.xp})
            
        return results
    
    def attack(self, target: Entity):
        results = []
        
        damage = self.power - target.fighter.defense
        
        if damage > 0:
            results.append({'message': Message('{0} attacks {1} for {2} hit points.'.format(
                self.owner.name.capitalize(), target.name, str(damage)))})
            results.extend(target.fighter.take_damage(damage))
        else:
            results.append({'message': Message('{0} attacks {1} but does no damage.'.format(
                self.owner.name.capitalize(), target.name))})
                
        return results
    
    def heal(self, amount):
        self.hp += amount
        
        if self.hp >= self.max_hp:
            self.hp = self.max_hp