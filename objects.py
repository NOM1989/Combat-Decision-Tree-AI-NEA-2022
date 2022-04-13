class CombatItem:
    '''Class representation of a combat item'''
    def __init__(self, item_id: int, name: str, count: int, item_range: range, turns: range, experience: range) -> None:
        self.id = item_id
        self.name = name
        self.count = count
        self.range = item_range
        self.turns = turns
        self.experience = experience

class PlayerItem:
    '''Class representation of a player item'''
    def __init__(self, item_id: int, name: str, quantity: int) -> None:
        self.id = item_id
        self.name = name
        self.count = quantity

class Player:
    '''Class representation of a player'''
    def __init__(self, player_id: int, name: str, max_health: int, coins: int, energy: int, experience: int) -> None:
        self.id = player_id
        self.name = name
        self.max_health = max_health
        self.coins = coins
        self.energy = energy
        self.experience = experience

class Ingredient:
    '''Class representation of an ingredient'''
    def __init__(self, item_id: int, quantity: int) -> None:
        self.item_id = item_id
        self.quantity = quantity

class ConsumableData:
    '''Class representation of Item consumable data'''
    def __init__(self,
        item_type: str = None,
        item_range: range = None,
        experience: range = None,
        turns: range = None
        ) -> None:
        
        self.type = item_type
        if item_range != None:
            self.range = item_range
        if experience != None:
            self.experience = experience
        if turns != None:
            self.turns = turns

class Item(ConsumableData):
    '''Class representation of an Item'''          
    def __init__(self,
            item_id: int,
            name: str,
            category: str,
            value: int,
            level: int,
            rarity: str,

            description: str = None,
            emoji: str = None,

            item_type: str = None,
            item_range: range = None,
            experience: range = None,
            turns: range = None
        ) -> None:
        super().__init__(item_type, item_range, experience, turns)

        self.id = item_id
        self.name = name
        self.description = description
        self.emoji = emoji
        self.category = category
        self.value = value
        self.level = level
        self.rarity = rarity