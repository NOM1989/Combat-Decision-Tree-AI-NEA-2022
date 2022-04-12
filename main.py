from psycopg2.extensions import (connection as PostgresConnection, cursor as PostgresCursor)
from difflib import get_close_matches
from dotenv import load_dotenv
from load_csv import Loader
from combat import Combat
from query import Connection
from setup import Setup
from os import getenv, path
import traceback
import psycopg2

class Menu(Connection):
    '''Class for common menu methods'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)

    def create_menu_options(self, options: dict[str, any]):
        '''Create a menu from the list of options, returning the corresponding function'''
        print('\nWhat would you like to do?')
        print('\n'.join([f'{index+1}. {option.capitalize()}' for index, option in enumerate(options)]))

        selection = get_close_matches(input('Select an option: '), options.keys(), n=1)
        while not selection:
            selection = get_close_matches(input('\nInvalid, please select an option: '), options.keys(), n=1)
        return options[selection[0]]
    
    def request_player_id(self):
        '''Prompts the user for a player_id, returning the corresponding Player or None if invalid'''
        player_id = input('Please enter a player id: ')
        player = self.querier.players.fetch_player(player_id)
        if player:
            return player 
        print('Player not found!')

    def back(self):
        '''No-Op funtion to return the user to the previous Menu'''
        return
        
class PlayerMenu(Menu):
    '''Menu for Player realted actions: `add/remove/view` player'''
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
        '''Adds a player to the DB, asking the user for a name'''
        name = input('Please enter a name for the new player: ')
        player = self.querier.players.add_player(name)
        print(f'Added player with id:name of \'{player.id}:{player.name}\' to the databse')

    def remove(self):
        '''Removes a player from the DB, asking the user for an id'''
        player = self.request_player_id()
        if player:
            self.querier.players.delete_player(player.id)
            print(f'Removed player with id:name of \'{player.id}:{player.name}\' from the databse')

    def player_list(self):
        '''Displays all the current players in the database'''
        print('\n'.join([f'{player.id}:{player.name}' for player in self.querier.players.fetch_players()]))

class InventoryMenu(Menu):
    '''Inventory menu'''
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
        '''Displays a player's Items, asking the user for an id'''
        player = self.request_player_id()
        if player:
            print(f'\n{player.name}\'s Items:')
            print('\n'.join([f'{item.name} x{item.count}' for item in self.querier.players.fetch_player_items(player.id)]))

    def get_player_and_item(self):
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

    def add(self):
        '''Asks the user for: a player_id, an item name or id and an amount.
            Then adds/updates the corresponding item to/in the PlayerItems table'''
        name_id_map, player, item_id = self.get_player_and_item()
        if player and item_id:
            amount = input('Enter an amount: ')
            while not amount.isdigit():
                amount = input('Invalid input, try again: ')
            id_name_map = {b: a for a, b in name_id_map.items()} #Reverse the name_id_map so we can recover the name
            print(f"'{player.name}' now has '{id_name_map[item_id]}' x{self.querier.players.update_player_item(player.id, item_id, amount)}")

    def delete(self):
        '''Asks the user for: a player_id and an item name or id.
            Then attempts to delete that entry from the players inventory (If it was present)'''
        name_id_map, player, item_id = self.get_player_and_item()
        if player and item_id:
            self.querier.players.delete_player_item(player.id, item_id)

class ItemMenu(Menu):
    '''Menu for Item related actions: `add/edit/remove` item'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)
        options = {
            'List': self.item_list,
            'Back': self.back
        }
        self.create_menu_options(options)()

    def item_list(self):
        '''Displays all the current items in the database'''
        print('\n'.join([f'{item.id}:{item.name}' for item in self.querier.items.fetch_items()]))

class CombatMenu(Menu):
    '''Combat menu'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)
        options = {
            'Combat': self.combat,
            'Back': self.back
        }
        self.create_menu_options(options)()

    def combat(self):
        '''Begin a combat instance, asking the user for player_id to use'''
        player = self.request_player_id()
        if player:
            return Combat(self.querier, player)

class SetupMenu(Menu):
    '''Setup menu'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)
        options = {
            'Setup': self.setup,
            'Load': self.load,
            'Back': self.back
        }
        self.create_menu_options(options)()

    def setup(self):
        '''Sets up the Databse for the game with all appropriate tables,
            dropping all existing tables beforehand'''
        Setup(self.conn, self.cur)
        print('Database has been setup!')
    
    def load(self):
        '''Loads items into the database from a csv file,
            asks the user for the file path'''
        csv_path = input('Please enter the path to the csv file: ')
        if csv_path.endswith('.csv') and path.isfile(csv_path):
            Loader(self.conn, self.cur, csv_path)
            return
        print('That file is not csv or does not exist!')

class QuitMenu(Menu):
    '''Exit the Program'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)
        exit()

class Main(Menu):
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)
        self.menu()

    def menu(self):
        '''Displays the main menu'''
        options = {
            'Players': PlayerMenu,
            'Inventory': InventoryMenu,
            'Items': ItemMenu,
            'Combat': CombatMenu,
            'Setup': SetupMenu,
            'Quit': QuitMenu
        }
        while True:
            self.create_menu_options(options)(self.conn, self.cur) #All menus take these params


if __name__ == '__main__':
    load_dotenv()
    db_username = getenv('DB_USERNAME')
    db_pass = getenv('DB_PASS')
    db_name = getenv('DB_NAME')
    db_host = getenv('DB_HOST')

    try:
        connection = psycopg2.connect(user=db_username,
            password=db_pass,
            host=db_host,
            database=db_name)
        connection.set_session(autocommit=True)
        cursor = connection.cursor()

        Main(connection, cursor)

    except (Exception, psycopg2.Error) as error:
        print(f"Error - {type(error).__name__}", error)
        traceback.print_tb(error.__traceback__)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")


# items = [
    #     'sparking',
    #     'blast of bones',
    #     'elemental explosion',
    #     'forest brew'
    # ]
    # for item in items:
    #     self.querier.players.update_item(self.querier.items.name_id_map, player_id, 2, item_name=item)