from __future__ import annotations
from collections import Counter
from psycopg2 import extras
from query import Querier, GameObjects
import psycopg2
import csv

class Loader():
    '''A class to load game data into the database from a csv file'''
    def __init__(self, querier, connection, cursor, csv_path) -> None:
        self.querier: Querier = querier
        self.conn: psycopg2.connection = connection
        self.cur: psycopg2.cursor = cursor
        self.add_items_from_csv(csv_path)
        self.add_recipes_from_csv(csv_path)

    def add_ConsumableData_query(self, item_type: str, item_range: range, experience: range, turns: range) -> int:
        '''Adds a row to the ConsumableData table, returning the generated consumable_id'''

        query = '''INSERT INTO ConsumableData(type, min_range, max_range, min_experience, max_experience, min_turns, max_turns)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING consumable_id;'''
        item_range.start
        self.cur.execute(query, (
            item_type,
            item_range.start,
            item_range.stop,
            experience.start,
            experience.stop,
            turns.start,
            turns.stop))
        return self.cur.fetchone()[0]

    def add_Item_query(self, name: str, category: str, value: int, level: int, rarity: str, description: str = None, emoji: str = None, consumable_id: int = None):
        '''Adds a row to the Items table, linking the ConsumableData foreign key if provided'''

        query = '''INSERT INTO Items(name, description, emoji, category, value, level, rarity, consumable_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);'''
        self.cur.execute(query, (name, description, emoji, category, value, level, rarity, consumable_id))

    def push_item(self, item: GameObjects.Item):
        '''Adds the `item` to the Items table, adding to the coresponding ConsumableData table if necessary'''
        consumable_id = None
        if item.type:
            consumable_id = self.add_ConsumableData_query(item.type, item.range, item.experience, item.turns)
        self.add_Item_query(item.name, item.category, item.value, item.level, item.rarity, item.description, item.emoji, consumable_id)

    def add_items_from_csv(self, csv_file):
        '''Loop through a csv file of format:
        Name,Value,rarity,level,category,type,R-from,R-to,XP-from,Xp-to,cooldown-from,cooldown-to,Recipe (csv)
        and add each item to the Database
        '''
        # Indexes:
        # Name,Value,rarity,level,category,type,R-from,R-to,XP-from,Xp-to,cooldown-from,cooldown-to,Recipe (csv)
        # 0      1     2      3       4      5     6     7    8       9      10             11          12
        with open(csv_file, newline='') as csvfile:
            file = csv.reader(csvfile)
            for row in file:
                item_type = row[5]
                item_range, experience, turns = None, None, None
                if item_type:
                    item_range = range(int(row[6]), int(row[7]))
                    experience = range(int(row[8]),int(row[9]))
                    turns = range(int(row[10]), int(row[11]))
                item = GameObjects.Item(
                    name=row[0],
                    category=row[4],
                    value=row[1],
                    level=int(row[3]),
                    rarity=row[2],
                    item_type=item_type,
                    item_range=item_range,
                    experience=experience,
                    turns=turns
                )
                self.push_item(item)

    def fetch_next_recipe_id(self) -> int:
        '''Fetch nect recipe_id from id sequence'''
        query = '''SELECT NEXTVAL('RecipesRecipeIdSequence');'''
        self.cur.execute(query)
        return self.cur.fetchone()[0]

    def add_ingredients_querys(self, recipe_id: int, recipe: list[GameObjects.Ingredient]):
        '''Adds many rows to the Recipes table respresenting each ingredient'''
        query = '''INSERT INTO Recipes
            VALUES %s;'''
        rows = []
        for ingredient in recipe:
            rows.append((recipe_id, ingredient.item_id, ingredient.quantity))
        extras.execute_values(self.cur, query, rows)

    def add_id_to_item_query(self, recipe_id: int, item_id: int):
        '''Updates the corresponding row in the Items table with the recipe_id of teh recipe we just added'''
        query = '''UPDATE Items
            SET recipe_id = %s
            WHERE item_id = %s;'''
        self.cur.execute(query, (recipe_id, item_id))

    def push_recipe(self, item_id, recipe: list[GameObjects.Ingredient]):
        '''Adds a recipe to a row in the Items table'''
        recipe_id = self.fetch_next_recipe_id()
        self.add_ingredients_querys(recipe_id, recipe)
        self.add_id_to_item_query(recipe_id, item_id)

    def add_recipes_from_csv(self, csv_file):
        '''Adds recipes to items from a csv file,
        has to be a separate function as we need the generated ids
        of the items we previously added to put them in the recipe'''
        name_id_map = self.querier.items.fetch_name_id_map()
        with open(csv_file, newline='') as csvfile:
            file = csv.reader(csvfile)
            for row in file:
                item_name = row[0]
                if row[12]: #Recipe
                    ingredients = Counter(row[12].split(','))
                    recipe: list[GameObjects.Ingredient] = []
                    for item in ingredients:
                        recipe.append(GameObjects.Ingredient(name_id_map[item], ingredients[item]))
                    self.push_recipe(name_id_map[item_name], recipe)
