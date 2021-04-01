from random import randint

def random_choice_index(chances):
    
    random_chance = randint(0, sum(chances))
    running_sum = 0
    choice = 0
    
    for weight in chances:
        running_sum += weight
        
        if random_chance <= running_sum:
            return choice
        
        choice += 1

def random_choice_from_dict(choice_dict):
    choices = list(choice_dict.keys())
    chances = list(choice_dict.values())
    
    return choices[random_choice_index(chances)]

def from_dungeon_level(table, dungeon_level):
    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value
        
    return 0