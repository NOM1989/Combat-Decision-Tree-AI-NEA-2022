from __future__ import annotations # Allows for type hinting of classes within themselves [https://stackoverflow.com/a/33533514]
from operator import attrgetter, methodcaller
from difflib import get_close_matches
from random import choice, randint, uniform
from query import Querier, GameObjects
from math import ceil

from copy import deepcopy

debug = True

class Combat:
    class Item(GameObjects.CombatItem):
        '''Class representation of a game item with methods'''
        def __init__(self, item_id: int, name: str, count: int, item_range: range, turns: range, experience: range) -> None:
            super().__init__(item_id, name, count, item_range, turns, experience)
            self.initial_count: int = int(count)
            self.current_chance: float | None = None # Used for processing
            self.tmp_count: int = None # Used for processing

        def get_range_avg(self):
            '''Return the range avg of the item'''
            return (self.range.stop + self.range.start)/2

        def get_turn_avg(self):
            '''Return the turn avg of the item'''
            return (self.turns.stop + self.turns.start)/2

        def get_range(self) -> int:
            '''Return the range of damage/healing the item can do'''
            return self.range.stop - self.range.start + 1
        
        def roll_amount(self):
            '''Simulates using the attack/heal, returning the amount'''
            return randint(self.range.start, self.range.stop)

        def roll_cooldown(self):
            '''Returns the rolled cooldown of the item'''
            return randint(self.turns.start, self.turns.stop)

        def get_count(self):
            '''Return the quantity of the item the instance has'''
            return self.count

        def reduce_count(self):
            '''Updated the count of that item'''
            self.count -= 1

    class BaseClass:
        def __init__(self, name, max_health, damaging, healing, health=None) -> None:
            self.name: str = name
            self.max_health: int = max_health
            self.health: int = health if health else max_health
            self.turn_cooldown: int = 0
            self.move_number: int = 0
            self.damaging: list[Combat.Item] = damaging
            self.healing: list[Combat.Item] = healing
            self.used: list[Combat.Item] = []

        def get_input(self, prompt: str = ''):
            return input(prompt)

        def ouput(self, text: str):
            print(text)

        def is_alive(self):
            '''Returns True if self is alive'''
            return bool(self.health)

        def on_cooldown(self):
            '''Returns True if self is on cooldown'''
            return bool(self.turn_cooldown)

        def update_cooldown(self, amount: int):
            '''Updates the turn_cooldown attribute by `amount`'''
            self.turn_cooldown += amount

        def increment_move_number(self):
            self.move_number += 1

        def health_lost(self):
            '''Returns the integer difference between health and max_health'''
            return abs(self.max_health - self.health) # Abs should be unnecessary as health should never be < 0
        
        def health_remaining_percentage(self):
            '''Returns a float between 0-1 respresenting the % of health remaing'''
            return self.health/self.max_health
        
        def health_lost_percentage(self):
            '''Returns a float between 0-1 respresenting the % of health lost'''
            return self.health_lost()/self.max_health

        # Generic function for below ones (too complex)
        # def get_minmax_for_method(self, items: list[Combat.Item], minmax: function, method):
        #     '''Returns the item that has the min/max result of method, depending on `function`
            
        #     `function`: should be `min` or `max`'''
        #     if function in (min, max):
        #         return function(items, key=methodcaller(method))
        #     raise TypeError('{function} must be {min} or {max}')

        def get_largest_range(self, items: list[Combat.Item]): #items -> eg. self.damaging or self.healing
            '''Returns the range of the item with the largest range'''
            return max(items, key=methodcaller('get_range')).get_range()
        
        def get_largest_range_avg(self, items: list[Combat.Item]):
            '''Returns the range avg of the item with the largest range avg'''
            return max(items, key=methodcaller('get_range_avg')).get_range_avg()

        def get_smallest_range(self, items: list[Combat.Item]):
            '''Returns the range of the item with the smallest range'''
            return min(items, key=methodcaller('get_range')).get_range()

        def get_closest_range_avg(self, items: list[Combat.Item], target_value: float):
            '''Returns the range_avg of the item in `items` that's range_avg is closest to `target_value`'''
            return min(items, key=lambda x:abs(x.get_range_avg()-target_value)).get_range_avg()
            # check/test this reurns the range_avg closest above not below

        def calculate_item_count(self, items: list[Combat.Item]):
            '''Returns the true count of how many items are 'in' items,
            this is necessary as Item objects have their own count attribute so simply calling len() would not suffice'''
            total = 0
            for item in items:
                total += item.count
            return total

        def get_n_items(self, items: list[Combat.Item], n: int = 1):
            '''Returns the first n items from items, taking into account the items count attribute

            `WARNING`: the count attribute from items returned by this function will not be accurate so is set to None,
            this is because we want a list of items to access their values rather than their count.'''
            if n <= self.calculate_item_count(items):
                items_list: list[Combat.Item] = []
                current_item = items.pop(0)
                current_item.tmp_count = int(current_item.count)
                while n:
                    if current_item.tmp_count < 1:
                        current_item = items.pop(0)
                        current_item.tmp_count = int(current_item.count)
                    items_list.append(current_item)
                    current_item.tmp_count -= 1
                    n -= 1
                for item in items_list:
                    item.tmp_count = None
                return items_list
            else:
                raise IndexError('Specified value of {n} greater than total {items} count.')

        def calculate_ranges_chance(self, item_range: range, value: int):
            '''Returns a float between 0 and 1 denoting the % of `item_range` that is >= `value`'''
            chance: float = 0
            if value in item_range:
                chance = (item_range.stop - value) / (len(item_range))
            return chance

        def get_highest_current_chance(self, items: list[Combat.Item]):
            '''Returns the item that had the higest `current_chance` attribute'''
            return max(items, key=attrgetter('current_chance'))

        def clear_current_chance_attributes(self, items: list[Combat.Item]):
            '''As items are processed the `current_chance` could be modified temporarily from None,
            this method resets all `current_chance` attrs to None'''
            for item in items:
                item.current_chance = None

        def ensure_move_available(self):
            '''Combat would break is one of then opponents had no moves,
            so if both damging and healing is empty then a default punch attack is added to the instance'''
            if self.damaging + self.healing == []:
                self.damaging.append(Combat.Item(None, 'punch', 1, range(0,1), range(1,2), range(0,0)))

        def remove_item(self, items: list[Combat.Item], item: Combat.Item):
            '''Reduces the count of an item in item_list or moves it to self.used if count is 0'''
            if item.name != 'punch': # If they are using the default punch attack do not remove
                item.reduce_count()
                if item.get_count() < 1:
                    items.remove(item)
                    self.used.append(item)
                self.ensure_move_available()
            return items
            
        def update_health(self, amount: int):
            '''Updates the health, returing the amount changed'''
            before = int(self.health)
            self.health = max(0, min(self.health+amount, self.max_health))
            return abs(before-self.health)

        def use_item(self, item: Combat.Item, target: Combat.BaseClass):
            ''''Uses' the `item` specified (on `target` - if attack)'''
            self.increment_move_number()
            amount = item.roll_amount()
            self.update_cooldown(item.roll_cooldown())
            if item in self.healing:                
                self.remove_item(self.healing, item)
                health_gained = self.update_health(amount)
                self.ouput(f'\n{self.name} healed themself with {item.name} gaining {health_gained} HP\n')
                return health_gained
            # else: an attack
            self.remove_item(self.damaging, item)
            dmg_dealt = target.update_health(-amount)
            self.ouput(f'\n{self.name} attacked {target.name} with {item.name} dealing {dmg_dealt} dmg\n')
            return dmg_dealt
            

    class Enemy(BaseClass):
        '''An AI controlled enemy for the player to face in combat'''
        def __init__(self, Player: Combat.BaseClass, damaging, healing, health=None, difficulty=None, risk=None) -> None:
            self.difficulty: float = difficulty if difficulty else round(uniform(0.25, 0.75), 3)
            super().__init__(self.generate_name(), self.calculate_max_health(Player.max_health), damaging, healing, health)
            self.risk: float = risk if risk else round(uniform(0.3, 0.85), 3) # The maximum risk enemy will take
            self.moves_to_predict: int = 2

        def debug(self, text: str):
            '''Displays debug information if debug is True'''
            global debug
            if debug:
                print(f'DEBUG: {self.__class__.__name__} - ' + text)
        
        def debug_display_items(self, items: list[Combat.Item]):
            return ', '.join([item.name for item in items])

        def calculate_max_health(self, player_max_health):
            '''Returns a maximum health for the enemy based on the difficulty'''
            return round(player_max_health + player_max_health*(self.difficulty-0.5))

        def get_difficulty_name(self):
            '''Returns the difficulty category the current enemy falls into (arbitarily chosen)'''
            if self.difficulty < 0.45:
                return 'easy'
            if self.difficulty < 0.65:
                return 'medium'
            return 'hard'

        def generate_name(self):
            '''Creates a randomised name for the enemy'''
            names = ('goblin', 'dark elf', 'ogre', 'witch', 'hog', 'spirit', 'gremlin')
            return f'{self.get_difficulty_name()} {choice(names)}'

        ## Generic Function ##
        def get_items_with_target_method_value(self, items: list[Combat.Item], value_to_match, method_to_get_value):
            '''Returns a list of items from `items` where the result of `method_to_get_value` matches `value_to_match`'''
            return [item for item in items if getattr(item, method_to_get_value)() == value_to_match]

        def find_items_likely_to_roll_required(self, items: list[Combat.Item], required_amount: int):
            '''Return a list of items most likely to roll the value of `required_amount` in `items`,
            these will be items that have a close range_avg and a narrow range.'''
            # Find items with range_avg that is closest to the required amount
            target_range_avg = self.get_closest_range_avg(items, required_amount)
            items_of_range_avg = self.get_items_with_target_method_value(items, target_range_avg, 'get_range_avg')

            # Of those items return the ones with the smallest range (most likely to roll nearest required amount)
            smallest_range = self.get_smallest_range(items_of_range_avg)
            items_of_smallest_range = self.get_items_with_target_method_value(items_of_range_avg, smallest_range, 'get_range')

            # items_of_smallest_range has been narrowed down a lot so it is likely this list contains only 1 item
            return items_of_smallest_range

        def select_percentage_of_list(self, items: list[Combat.Item], percentage: float):
            '''Returns the first x% of items in `items`, will always return at least one item'''
            return items[:ceil(len(items)*percentage)]

        def normal_move(self, player: Combat.Player):
            '''Returns an Item the enemy should use,
            There are no immediate opportunities/dangers so this is a broarder move.
            
            The choice of move is made based off multiple factors:
            
            % Enemy health lost > risk --> enemy could heal (lower difficulty more likely to heal)


            Define lower and higher player health as a %:
                split around 50% with some variation
                0.5 + (0.5-difficulty)/2:
                    higher difficulty (.75) --> 0.375 more likely to save stronger attacks for later (less time to react/heal)
                    lower difficulty (.25) --> 0.625 more likely to use stronger attacks earlier on (more time to react/heal)

            higher player health --> use larger range attacks
            lower player health --> use stonger attacks


            Define how to choose and attack:
            possible options = 0.5 + (0.5-diff)/(3/2) % of attacks that meet criteria
                higher difficulty (.75) --> 33.3% more likely to use attack that meets criteria
                lower difficulty (.25) --> 66.6% less likely to use attack that meets criteria

            then of possible options:
                High health of enemy --> can use attacks with larger cooldowns
                use threshold to decide if enemy on higher or lower health
                    higher --> sort by highest avg cooldown to lowest avg cooldown
                    lower --> sort by lowest avg cooldown to highest avg cooldown

                    then use 0.5 + (0.5-diff)/(3/2) % again to get the fist % items in that list and randomly pick one
                    automatically put the first item in the list then check if % above required and if not add more (ensures % is not too low)
            
            
            if enemy has attacks:
                above checks
                if enemy has healing, compare healing
                return attack/heal
            if enemy has heal:
                return most adequate heal
            else:
                will never occurr.
            '''
            if not self.healing and not self.damaging:
                raise RuntimeError('Both self.damaging and self.healing are empty, no move to make')

            self.debug('-> Now attempting normal_move')

            selected_attack = None
            if self.damaging:
                # We need to decide if the player is on 'lower' or 'higher' health,
                # this is roughly 50% of max_health with some variation based on the enemys dificulty.
        
                health_threshold = 0.5 + (0.5-self.difficulty)/2
                    # higher difficulty (.75) --> 0.375 more likely to save stronger attacks for later (less time for player react/heal)
                    # lower difficulty (.25) --> 0.625 more likely to use stronger attacks earlier on (more time for player react/heal)

                if player.health_remaining_percentage() < health_threshold:
                    self.debug("Player has 'lower' health -> attempting to use stonger attacks")
                    # Sort self.damaging by range_avg (largest first)
                    self.damaging.sort(key=methodcaller('get_range_avg'), reverse=True)
                else:
                    self.debug("Player has 'higher' health -> attempting to use larger range attacks")
                    # Sort self.damaging by range (largest first)
                    self.damaging.sort(key=methodcaller('get_range'), reverse=True)
                

                # Now we want to select a % of those attacks
                percentage_of_attacks_to_select = 0.5 + (0.5-self.difficulty)/(3/2)
                    # higher difficulty (.75) --> 33.3% of attacks chosen, more likely to use attack that meets criteria
                    # lower difficulty (.25) --> 66.6% of attacks chosen, less likely to use attack that meets criteria

                selected_attacks = self.select_percentage_of_list(self.damaging, percentage_of_attacks_to_select)
                self.debug(f'Selected {len(selected_attacks)} possible attack(s): {self.debug_display_items(selected_attacks)}')


                # Now we decide if the enemy is on 'lower' or 'higher' health, based on same threshold as above
                if self.health_remaining_percentage() < health_threshold:
                    self.debug("I have 'lower' health -> sort my attacks by lowest to highest avg cooldown")
                    reverse = False
                else:
                    self.debug("I have 'higher' health -> sort my attacks by highest to lowest avg cooldown")
                    reverse = True


                selected_attacks.sort(key=methodcaller('get_turn_avg'), reverse=reverse)

                # Select another % of those attacks (same % as before)
                # Then randomly select one from this heavily narrowed down list
                # We have narrowed it down so much it is highly unlikely this final list contains more than 1 attack
                selected_attack = choice(self.select_percentage_of_list(selected_attacks, percentage_of_attacks_to_select))
                self.debug(f'Selected best suited attack as: {selected_attack.name}')
                
                # Now we have a good attack for the current situation
                # However we also want to take into account the enemys health
                
                self.debug('Checking to see if heaing would be more benificial')

                # So we check if health_lost % is > risk and if so, enemy will consider healing
                if not self.healing or self.health_lost_percentage() < self.risk:
                    # Enemy's health is above risk threshold, no need to heal
                    # OR enemy has no heals
                    # Use suitable attack we found earlier
                    self.debug(f'No need to heal / I have no healing, using attack: {selected_attack.name}')
                    return selected_attack

                # Else - Have lost a % of health that outweighs risk enemy wants to take
                # So now find healings that would remedy...
                self.debug(f'I have lost {round(self.health_lost_percentage()*100)}% which is lower than my risk allows, finding potential heal')

            # !!! Notice the indentation difference, the following will happen even if the enemy never had any attacks !!!

            # We now select a heal as the function would have returned already if a previous condition had been met
            likely_perfect_healing_items = self.find_items_likely_to_roll_required(self.healing, self.health_lost())
            # select a random one (choice is likey from a list of 1 as heals have been narrowed down)
            selected_heal = choice(likely_perfect_healing_items)
            self.debug(f'Selected likely perfect heal: {selected_heal.name}')
            

            if selected_attack:
                self.debug('Comparing attack to heal to see which is more effective')
                # Now we have 'the perfect' heal and 'the perfect' attack
                # Lets compare which one would be more effective, based on the change to the recipients health
                percentage_change_in_player_health = selected_attack.get_range_avg()/player.max_health
                percentage_change_in_enemy_health = selected_heal.get_range_avg()/self.max_health

                if percentage_change_in_player_health > percentage_change_in_enemy_health:
                    self.debug(f'Decided attack is more effective: {selected_attack.name}')
                    return selected_attack

            # Else there are no attacks or healing is more effective, so return the selected heal (to use)
            self.debug(f'Decided to use heal (potentially most effective): {selected_heal.name}')
            return selected_heal

        def get_overlapping_items(self, items: list[Combat.Item], health: int):
            '''Return a list of items where the item range overlaps with the `health` passed if the overlap is above self.risk
            `items`: list of (attack) items
            `health`: health of the enemy or player'''
            dangerous_items: list[Combat.Item] = []
            for item in items:
                items_current_chance = self.calculate_ranges_chance(item.range, health)
                # self.debug(f'-> {item.name} chance to kill player: {items_current_chance}')
                if items_current_chance > self.risk:
                    item.current_chance = items_current_chance
                    dangerous_items.append(item)
            return dangerous_items
        
        def can_player_be_killed(self, player: Combat.Player):
            '''Checks if the player can be killed in the next move, returing potential attacks if so'''
            self.debug('Looking for items that can kill player this turn')
            return self.get_overlapping_items(self.damaging, player.health)

        # def get_items_with_max_avg(self, items: list[Combat.Item]):
        #     '''Returns a list of items from `items` where the max_avg matches the maximum avg of `items`'''
        #     current_max_avg = self.get_largest_range_avg(items)
        #     return [item for item in items if item.get_range_avg() == current_max_avg]

        def get_items_with_max_range_avg(self, items: list[Combat.Item]): # A specific version of the get_items_with_target_method_value() method
            '''Returns a list of items from `items` where the value of the items' range_avg matches the largest range avg in `items`'''
            largest_range_avg = self.get_largest_range_avg(items)
            # self.debug(f'Largest range avg: {largest_range_avg}')
            return [item for item in items if item.get_range_avg() == largest_range_avg]
        
        def get_items_with_max_range(self, items: list[Combat.Item]): # A specific version of the get_items_with_target_method_value() method
            '''Returns a list of items from `items` where the value of the items' range matches the largest range in `items`'''
            largest_range = self.get_largest_range(items)
            # self.debug(f'Largest range: {largest_range}')
            return [item for item in items if item.get_range() == largest_range]

        def make_move(self, player: Combat.Player) -> Combat.Item:
            '''This is called everytime the enemy should make a move, 
            it returns an Item from either self.damaging or self.healing to be used'''

            # Look for attack that can kill player this move, otherwise move on
            possible_kill_attacks = self.can_player_be_killed(player)
            if possible_kill_attacks:
                # Uses the attack with the highest current_chance of killing,
                # current_chance will be above risk if it is in possible_kill_attacks
                most_likely_kill_attack = self.get_highest_current_chance(possible_kill_attacks)
                self.clear_current_chance_attributes(possible_kill_attacks)
                self.debug(f'Found attack that can kill player this move: {most_likely_kill_attack.name}')
                return most_likely_kill_attack
            
            # Find most dangerous attacks to me
            # These will be the ones with the highest avg dmg, then largest range (to account for worst case)

            max_avg_selections = []
            max_range_selections = []
            dangerous_player_items = []
            player_attacks_count = self.calculate_item_count(player.damaging)
            moves_to_predict = self.moves_to_predict if player_attacks_count >= self.moves_to_predict else player_attacks_count
            while self.calculate_item_count(dangerous_player_items) < moves_to_predict:
                if not max_range_selections:
                    if not max_avg_selections:
                        max_avg_selections = self.get_items_with_max_range_avg(player.damaging)
                        # self.debug(f'max_avg_selections: {max_avg_selections}')
                    max_range_selections = self.get_items_with_max_range(max_avg_selections)
                    max_range_selections.sort(key=methodcaller('get_turn_avg')) #Check if this sorts into the correct way around
                    
                selection = max_range_selections.pop(0)
                dangerous_player_items.append(selection)
                max_avg_selections.remove(selection)
                player.damaging.remove(selection)
                # self.debug(f'Identified {selection} as dangerous item')

            # Player item processing complete, return player items
            for item in dangerous_player_items:
                player.damaging.append(item)

            dangerous_player_items = self.get_n_items(dangerous_player_items, n=self.moves_to_predict)
            self.debug(f"Player items dangerous to me: {self.debug_display_items(dangerous_player_items)}")

            in_range_count = 0
            total_possible_count = dangerous_player_items[0].get_range() * dangerous_player_items[1].get_range()
            for number in dangerous_player_items[0].range:
                for number2 in dangerous_player_items[1].range:
                    if number + number2 >= self.health:
                        in_range_count += 1

            self.debug(f'There is a {round(in_range_count/total_possible_count*100)}% chance I die in the next 2 player moves')
            if in_range_count/total_possible_count > self.risk:
                # Attempt to heal, when healing we want to find the perfect healing for the situation
                self.debug(f'Attempting to heal')
                if self.health_lost() and self.healing:
                    likely_perfect_healing_items = self.find_items_likely_to_roll_required(self.healing, self.health_lost())
                    # Pick the one with lowest avg turns cooldown
                    heal_to_use = min(likely_perfect_healing_items, key=methodcaller('get_turn_avg')) # the heal to use
                    self.debug(f'Selected {heal_to_use.name} as the heal to use')
                    return heal_to_use
                self.debug('Cannot heal, moving on')
            
            # If this point is reached:
            # - Enemy cannot kill player next move
            # - Player cannot kill enemy in self.moves_to_predict moves
            self.debug(f'I cannot kill player next move, player cannot kill me in {self.moves_to_predict} moves (based on risk)')

            # --> Normal attack should be carried out
            return self.normal_move(player)
        
    class Player(BaseClass):
        '''The human controlled player in combat'''
        def __init__(self, player_id: int, name: str, max_health: int, damaging: list[Combat.Item], healing: list[Combat.Item], health=None) -> None:
            super().__init__(name, max_health, damaging, healing, health)
            self.id = player_id
            self.item_names: list[str] = []

        def get_all_items(self):
            '''Returns a combined list of all the players items'''
            return self.damaging + self.healing

        def update_item_names(self):
            '''Updates self.item_names to a list with all the names of the items the player currently has'''
            names: list[str] = []
            for item in self.get_all_items():
                names.append(item.name)
            self.item_names = names

        def get_selection(self):
            '''Returns the name of the item selected by the player or None if not found'''
            possible_selction = get_close_matches(self.get_input('Enter the item you wish to use: '), self.item_names, n=1)
            if possible_selction:
                return possible_selction[0]
            return None

        def match_name_to_item(self, name: str) -> Combat.Item:
            for item in self.get_all_items():
                if item.name == name:
                    return item

        def make_move(self):
            '''Prompts the player for an item to use this move'''
            self.update_item_names()
            selection = self.get_selection()
            while not selection:
                self.ouput('Item not found! Try again...')
                selection = self.get_selection()
            return self.match_name_to_item(selection)

    ###################################################################################

    def __init__(self, querier, player: GameObjects.Player) -> None:
        self.querier: Querier = querier
        damaging, healing = self.querier.players.fetch_combat_items(player.id)

        # Map returned items to combat items with methods
        damaging = [Combat.Item(item.id, item.name, item.count, item.range, item.turns, item.experience) for item in damaging]
        healing = [Combat.Item(item.id, item.name, item.count, item.range, item.turns, item.experience) for item in healing]
        
        # Create an instance of player and enemy
        self.player: Combat.Player = self.Player(player.id, player.name, player.max_health, damaging, healing)
        self.enemy: Combat.Enemy = self.Enemy(self.player, deepcopy(damaging), deepcopy(healing))
        self.instances: list[Combat.BaseClass] = (self.player, self.enemy)
        print('Beginning Combat!\n')
        self.enemy.debug(f'DIFFICULTY: {self.enemy.difficulty} - RISK: {self.enemy.risk}')
        self.main()

    def ouput(self, text: str):
        print(text)

    def instances_are_alive(self):
        '''Returns true if all instances in self.instances are alive (health > 0)'''
        for instance in self.instances:
            if not instance.is_alive():
                return False
        return True
        
    def reduce_cooldowns(self):
        '''Reduces the cooldown of all instances in self.instances'''
        for instance in self.instances:
            instance.update_cooldown(-1)

    def create_display_divider(self, text: str, extra: int = 0):
        '''Returns a series of '-'s of length len(`text`)+`extra`'''
        return '-'*(len(text)+extra)

    def display_items(self, items: list[Combat.Item]):
        '''Returns a stiring representation of `items`'''
        display_strings = []
        for item in items:
            display_strings.append(f'{item.name} - [{item.range.start},{item.range.stop}] x{item.count}')
        return '\n'.join(display_strings)

    def display_combat(self):
        '''Display current information about each player,
        including health and items'''
        for instance in self.instances:
            self.ouput(f"{self.create_display_divider(instance.name, 8)}\n\
{instance.name} {instance.health}/{instance.max_health} HP\n\
{self.create_display_divider(instance.name, 8)}\n\n\
Attacks\n\
{self.create_display_divider('Attacks')}\n\
{self.display_items(instance.damaging)}\n\n\
Heals\n\
{self.create_display_divider('Heals')}\n\
{self.display_items(instance.healing)}\n\
            ")
            
    def display_winner(self):
        '''Display the winner of the Combat'''
        player, enemy = self.player, self.enemy
        self.ouput('\n\nEnd of Combat!')
        if enemy.is_alive():
            self.ouput(f"You were defeated by the {enemy.name}!")
        else:
            self.ouput(f"Congratulations {player.name}, you defeated the {enemy.name}!")
        self.ouput(f'{player.name} made {player.move_number} moves while {enemy.name} made {enemy.move_number} moves')

    def update_db_items(self, player: Combat.Player):
        '''Updates the players items in the DB to reflect the changes after some were used in Combat'''
        for item in player.damaging + player.healing + player.used:
            if item.initial_count != item.count: # Dont unnecessarily update the DB
                self.querier.players.set_or_delete_player_item(player.id, item.id, item.initial_count-item.count)

    def main(self):
        while self.instances_are_alive():
            if not self.player.on_cooldown():
                self.display_combat()
                self.player.use_item(self.player.make_move(), self.enemy)

            if not self.enemy.on_cooldown() and self.enemy.is_alive(): # Enemy may have died on players turn
                self.enemy.use_item(self.enemy.make_move(self.player), self.player)
                # self.display_combat()

            self.reduce_cooldowns()
        self.display_winner()
        self.update_db_items(self.player) # Update the db to remove used items
        self.ouput(f'All items used in combat have been removed from {self.player.name}\'s inventory!')






###############################################################
# Attempt at writing code to simulate all possible moves,     #
# However the time complexity was too great so was abanadoned #
###############################################################
    # def _get_items_with_cooldown(self, move_list: list, target_cooldown: int):
    #     '''Returns a list of Item instances from the move_list that have turn cooldowns (Item.turns) that overlap with the target_cooldown
    #     `move_list`: an instances' damaging or healing list'''
    #     within_cooldown = []
    #     for item in move_list:
    #         if item.turns[0] <= target_cooldown <= item.turns[1]:
    #             within_cooldown.append(item)
    #     return within_cooldown

    # def _calculate_range_counts(self, items: list):
    #     '''Loop through all items in items and total all the possible damages in a Counter object'''
    #     return Counter([dmg for range_list in (range(item.range[0], item.range[1]+1) for item in items) for dmg in range_list])

    # def simulate_items(self, items: list, depth: int = 2):
    #     '''Simulates using every combination of attacks the player can use to a specified depth (number of turns)
    #     sum damages possible and at what turns...?
    #     '''
    #     running_range_counts = Counter()
    #     for current_turn_to_simulate in range(depth):
    #         new_items = self._get_items_with_cooldown(items, current_turn_to_simulate)
    #         running_range_counts += self._calculate_range_counts(new_items)

    #         print(running_range_counts)
###############################################################