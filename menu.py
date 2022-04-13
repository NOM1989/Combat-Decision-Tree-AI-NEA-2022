from psycopg2.extensions import (connection as PostgresConnection, cursor as PostgresCursor)
from difflib import get_close_matches
from query import Connection
from combat import Combat
from load import Loader
from setup import Setup
from os import path

class Menu(Connection):
    '''Class for common menu methods'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)

    def create_menu_options(self, options: dict[str, any]):
        '''Create a menu from the list of options, returning the corresponding function'''
        print('\nWhat would you like to do?')
        print('\n'.join([f'{index+1}. {option:<9} - {options[option].__doc__}' for index, option in enumerate(options)]))

        selection = get_close_matches(input('\nSelect an option: '), options.keys(), n=1)
        while not selection:
            selection = get_close_matches(input('Invalid, please select an option: '), options.keys(), n=1)
        return options[selection[0]]
    
    def request_player_id(self):
        '''Prompts the user for a player_id, returning the corresponding Player or None if invalid'''
        player_id = input('Please enter a player id: ')
        while not player_id.isdigit():
            player_id = input('Invalid id, enter a player id: ')
        player = self.querier.players.fetch_player(player_id)

        if player:
            return player

        print('Player not found!')
        return None

    def back(self):
        '''return to the main menu'''
        return

class SetupMenu(Menu):
    '''actions relating to setting up the database'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)
        options = {
            'Setup': self.setup,
            'Load': self.load,
            'Back': self.back
        }
        self.create_menu_options(options)()

    def setup(self):
        '''sets up the Databse with all appropriate tables, dropping all existing tables beforehand'''
        Setup(self.conn, self.cur)
        print('\nDatabase setup successfully!')
    
    def load(self):
        '''loads items into the database from a csv file'''
        csv_path = input('Please enter the path to the csv file: ')
        if csv_path.endswith('.csv') and path.isfile(csv_path):
            Loader(self.conn, self.cur, csv_path)
            return
        print('That file is not csv or does not exist!')

class PlayerMenu(Menu):
    '''actions relating to Player objects'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)
        options = {
            'Add': self.add,
            'Remove': self.remove,
            'List': self.player_list,
            'Back': self.back
        }
        self.create_menu_options(options)()

    def add(self):
        '''adds a player to the DB'''
        name = input('Please enter a name for the new player: ')
        while not name.isalpha():
            name = input('Invalid name! Please enter a name: ')
        player = self.querier.players.add_player(name)
        print(f"\nAdded player with id:name of '{player.id}:{player.name}' to the database")

    def remove(self):
        '''removes a player from the DB'''
        player = self.request_player_id()
        if player:
            self.querier.players.delete_player(player.id)
            print(f"\nRemoved player with id:name of '{player.id}:{player.name}' from the databse")

    def player_list(self):
        '''displays all current players in the database'''
        print('\nAll Players:')
        print('\n'.join([f'{player.id}:{player.name}' for player in self.querier.players.fetch_players()]))

class InventoryMenu(Menu):
    '''actions relating to Player Inventories'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)
        options = {
            'View': self.view,
            'Add': self.add,
            'Delete': self.delete,
            'Back': self.back
        }
        self.create_menu_options(options)()

    def view(self):
        '''displays a player's Items'''
        player = self.request_player_id()
        if player:
            print(f"\n{player.name}'s Items:")
            print('\n'.join([f'{item.name} x{item.count}' for item in self.querier.players.fetch_player_items(player.id)]))

    def _get_player_and_item(self):
        '''Prompts the user for a player id and an item,
            also returns a name_id_map to save us fetching it again'''
        player = self.request_player_id()
        if player:
            name_or_id = input('Enter an item name or id: ')
            name_id_map = self.querier.items.fetch_name_id_map()
            item_id = self.querier.items.get_item_id(name_id_map, name_or_id)
            if item_id:
                return name_id_map, player, item_id
            print('Invalid item name or id!')
            return name_id_map, player, None
        return None, None, None

    def add(self):
        '''adds/updates an item to/in a Players inventory'''
        name_id_map, player, item_id = self._get_player_and_item()
        if player and item_id:
            amount = input('Enter an amount: ')
            while not amount.isdigit():
                amount = input('Invalid input, try again: ')
            id_name_map = {b: a for a, b in name_id_map.items()} #Reverse the name_id_map so we can recover the name
            print(f"\n'{player.name}' now has '{id_name_map[item_id]}' x{self.querier.players.update_player_item(player.id, item_id, amount)}")

    def delete(self):
        '''deletes an entry from a players inventory (if present)'''
        name_id_map, player, item_id = self._get_player_and_item()
        if player and item_id:
            id_name_map = {b: a for a, b in name_id_map.items()} #Reverse the name_id_map so we can recover the name
            self.querier.players.delete_player_item(player.id, item_id)
            print(f"\nRemoved all '{id_name_map[item_id]}' items from player '{player.name}'")

class ItemMenu(Menu):
    '''actions relating to Item objects'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)
        options = {
            'List': self.item_list,
            'Back': self.back
        }
        self.create_menu_options(options)()

    def item_list(self):
        '''displays all current items in the database'''
        print('\nAll Items:')
        print('\n'.join([f'{item.id}:{item.name}' for item in self.querier.items.fetch_items()]))

class CombatMenu(Menu):
    '''start a Combat instance'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)
        player = self.request_player_id()
        if player:
            Combat(connection, cursor, player)

class QuitMenu(Menu):
    '''exit the program'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)
        exit()

class MainMenu(Menu):
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)
        # Display the main menu
        options = {
            'Setup': SetupMenu,
            'Players': PlayerMenu,
            'Inventory': InventoryMenu,
            'Items': ItemMenu,
            'Combat': CombatMenu,
            'Quit': QuitMenu
        }
        while True:
            self.create_menu_options(options)(self.conn, self.cur) #All menus take these params