from psycopg2.extensions import (connection as PostgresConnection, cursor as PostgresCursor)
from query import BaseConnection

class Setup(BaseConnection):
    '''Setup class containing functions to setup the required tables in a database'''
    def __init__(self, connection: PostgresConnection, cursor: PostgresCursor) -> None:
        super().__init__(connection, cursor)

        # Remove any previous tables
        self.clear_previous_tables()

        # Setup all required tables and links
        self.create_player_items_table()
        self.create_player_table()
        self.create_game_data_tables()

    def clear_previous_tables(self):
        '''Drops all named tables in the DB'''
        querys = ('DROP TABLE IF EXISTS Players;',
            'DROP TABLE IF EXISTS PlayerItems;',
            'DROP TABLE IF EXISTS Recipes;',
            'DROP TABLE IF EXISTS Items;',
            'DROP TABLE IF EXISTS ConsumableData;')
        for query in querys:
            self.cur.execute(query)

    def create_player_items_table(self):
        '''Creates the table to store player inventories'''
        query = '''CREATE TABLE IF NOT EXISTS PlayerItems (
            player_id BIGINT NOT NULL,
            item_id SMALLINT NOT NULL,
            quantity SMALLINT DEFAULT 1 NOT NULL,
            PRIMARY KEY(player_id, item_id)
        );'''
        self.cur.execute(query)
    
    def create_player_table(self):
        '''Creates the table to store players and player information'''
        query = '''CREATE TABLE IF NOT EXISTS Players (
            player_id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            name VARCHAR NOT NULL,
            max_health SMALLINT DEFAULT 10,
            coins INT DEFAULT 1000,
            energy SMALLINT DEFAULT 0,
            experience INT DEFAULT 0
        );'''
        self.cur.execute(query)

    def create_game_data_tables(self):
        '''Creates the table to store game item information'''
        query = '''CREATE TABLE IF NOT EXISTS ConsumableData (
            consumable_id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            type VARCHAR NOT NULL,
            min_range SMALLINT,
            max_range SMALLINT,
            min_experience SMALLINT,
            max_experience SMALLINT,
            min_turns SMALLINT,
            max_turns SMALLINT,
            CONSTRAINT if_min_range_then_check_max_range_greater_or_equal CHECK ( (min_range IS NULL) OR (max_range >= min_range) ),
            CONSTRAINT if_min_experience_then_check_max_experience_greater_or_equal CHECK ( (min_experience IS NULL) OR (max_experience >= min_experience) ),
            CONSTRAINT if_min_turns_then_check_max_turns_greater_or_equal CHECK ( (min_turns IS NULL) OR (max_turns >= min_turns) )
        );'''
        self.cur.execute(query)
        
        query = '''CREATE TABLE IF NOT EXISTS Items (
            item_id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            name VARCHAR NOT NULL UNIQUE,
            description VARCHAR,
            emoji VARCHAR,
            category VARCHAR NOT NULL,
            value SMALLINT NOT NULL,
            level SMALLINT NOT NULL,
            rarity VARCHAR NOT NULL CONSTRAINT valid_rarity CHECK (rarity IN ('legendary', 'mythic', 'epic', 'rare', 'uncommon', 'common')),
            recipe_id SMALLINT,
            consumable_id SMALLINT,
            CONSTRAINT fk_ConsumableData
                FOREIGN KEY(consumable_id) 
                REFERENCES ConsumableData(consumable_id)
                ON DELETE SET NULL
        );'''
        self.cur.execute(query)

        query = '''CREATE SEQUENCE IF NOT EXISTS RecipesRecipeIdSequence;'''
        self.cur.execute(query)

        query = '''CREATE TABLE IF NOT EXISTS Recipes (
            recipe_id SMALLINT NOT NULL,
            item_id SMALLINT NOT NULL,
            quantity SMALLINT DEFAULT 1 NOT NULL,
            PRIMARY KEY (recipe_id, item_id)
        );'''
        self.cur.execute(query)

        query = '''ALTER SEQUENCE RecipesRecipeIdSequence OWNED BY Recipes.recipe_id;'''
        self.cur.execute(query)