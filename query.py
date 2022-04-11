from __future__ import annotations
import psycopg2

class GameObjects():
    '''Overarching class for common game object structures'''
    class CombatItem():
        '''Class representation of a combat item'''
        def __init__(self, item_id: int, name: str, count: int, item_range: range, turns: range, experience: range) -> None:
            self.id = item_id
            self.name = name
            self.count = count
            self.range = item_range
            self.turns = turns
            self.experience = experience

    class Player():
        '''Class representation of a player'''
        def __init__(self, player_id: int, name: str, max_health: int, coins: int, energy: int, experience: int) -> None:
            self.id = player_id
            self.name = name
            self.max_health = max_health
            self.coins = coins
            self.energy = energy
            self.experience = experience

    class Ingredient():
        '''Class representation of an ingredient'''
        def __init__(self, item_id: int, quantity: int) -> None:
            self.item_id = item_id
            self.quantity = quantity

    class ConsumableData():
        '''Class representation of an Item's consumable data'''
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

            self.name = name
            self.description = description
            self.emoji = emoji
            self.category = category
            self.value = value
            self.level = level
            self.rarity = rarity

class Connection():
    '''Base class for the DB connection and cursor'''
    def __init__(self, connection: psycopg2.connection, cursor: psycopg2.cursor) -> None:
        self.conn = connection
        self.cur = cursor

class Querier(Connection):
    '''An enclosing class for all queries, allows easy, indexed access to objects attributes via query lookups in the DB'''
    def __init__(self, connection: psycopg2.connection, cursor: psycopg2.cursor) -> None:
        super().__init__(connection, cursor)
        self.items = Items(self.conn, self.cur)
        self.players = Players(self.conn, self.cur)

class Items(Connection):
    '''Encompassing class for common item methods'''
    def __init__(self, connection: psycopg2.connection, cursor: psycopg2.cursor) -> None:
        super().__init__(connection, cursor)

    def _fetch_name_id_query(self):
        '''Selects the name and item_id of all items in the Items table'''
        query = '''SELECT name, item_id
            FROM Items;'''
        self.cur.execute(query)
        return self.cur.fetchall()

    def fetch_name_id_map(self):
        '''Fetch and generate a name to id map for all items in the Items table
        Returns a `dict: [names, item_ids]`'''
        name_id_map: dict[str, int] = {}
        for row in self._fetch_name_id_query():
            name_id_map[row[0]] = row[1]
        return name_id_map


class Players(Connection):
    '''Class representing a player object, fetches data from DB'''
    def __init__(self, connection: psycopg2.connection, cursor: psycopg2.cursor) -> None:
        super().__init__(connection, cursor)

    # def ensure_player(self, player_id):
    #     '''Queries the DB for the specified player and if not found creates a new one'''
    #     query = '''SELECT player_id
    #         FROM Players
    #         WHERE player_id = %s;'''
    #     self.cur.execute(query, (player_id,))
    #     res = self.cur.fetchone()

    #     if not res: # Player does not exist
    #         query = '''INSERT INTO Players(player_id)
    #             VALUES (%s);'''
    #         self.cur.execute(query, (player_id,))

    def _fetch_player_query(self, player_id):
        '''Fetches data for the specified player_id from the DB'''
        query = '''SELECT name, max_health, coins, energy, experience
            FROM Players
            WHERE player_id = %s;'''
        self.cur.execute(query, (player_id,))
        return self.cur.fetchone()

    def fetch_player(self, player_id: int):
        '''Returins a Player object, with every attribute in the DB represented'''
        res = self._fetch_player_query(player_id)
        return GameObjects.Player(player_id, res[0], res[1], res[2], res[3], res[4])

    def _delete_item_query(self, player_id: int, item_id: int):
        '''Deletes the specified item for the specified player from the PlayerItems table'''
        
        query = '''DELETE FROM PlayerItems
            WHERE player_id = %s AND
            item_id = %s;'''
        self.cur.execute(query, player_id, item_id)

    def _set_item_query(self, player_id: int, item_id: int, amount: int):
        '''Sets the quantity of the specified item, for the specified player in the PlayerItems table'''
        
        query = '''UPDATE PlayerItems
            SET quantity = %s
            WHERE player_id = %s AND
            item_id = %s;'''
        self.cur.execute(query, (amount, player_id, item_id))

    def set_or_delete_item(self, player_id: int, item_id: int, amount: int):
        '''Sets the quantity of the specified player's item to `amount`,
        if the amount is <= 0 the item is removed from the PlayerItems table.
        Note: Assumes the item is in the PlayerItems table'''
        if amount <= 0: # Delete the row from the DB
            return self._delete_item_query(player_id, item_id) # Not actually looking to return anything just a neat way to break
        # else: Set quantity to required amount
        self._set_item_query(player_id, item_id, amount)

    def _update_item_query(self, player_id: int, item_id: int, amount: int) -> int:
        '''Attempts to update the quantity of an item in the PlayerItems table,
        returing the new total'''
        
        query = '''UPDATE PlayerItems
            SET quantity = quantity + %s
            WHERE player_id = %s AND
            item_id = %s
            RETURNING quantity;'''
        self.cur.execute(query, (amount, player_id, item_id))
        return self.cur.fetchone()[0]

    def _add_item_query(self, player_id: int, item_id: int, amount: int):
        '''Adds the item to the specified player in the PlayerItems table'''
        
        query = '''INSERT INTO PlayerItems
            VALUES (%s, %s, %s);'''
        self.cur.execute(query, (player_id, item_id, amount))

    def update_item(self, player_id, amount, item_name=None, item_id=None, name_id_map: dict[str, int] = None):
        '''Adds or Updates an item to/in a players inventory, returning the new item quantity'''
        if not item_name and not item_id:
            raise ValueError('{item_name} or {item_id} must be present to look up an item')
        if item_name and not name_id_map:
            raise ValueError('{name_id_map} must be present to look up an item via {item_name}')

        if item_name:
            item_id = name_id_map[item_name]

        quantity = self._update_item_query(player_id, item_id, amount)
        if not quantity:
            # Data is not in DB and needs to be added
            self._add_item_query(player_id, item_id, amount)
            quantity = amount
        return quantity

    def _fetch_combat_items_query(self, player_id: int):
        '''Selects all item attributes required in combat for a specified player_id'''

        query = '''SELECT type, Items.item_id, name, quantity, min_range, max_range, min_turns, max_turns, min_experience, max_experience
            FROM Items
            INNER JOIN PlayerItems ON Items.item_id = PlayerItems.item_id
            INNER JOIN ConsumableData ON Items.consumable_id = ConsumableData.consumable_id
            WHERE Items.item_id IN (
                SELECT PlayerItems.item_id
                FROM PlayerItems
                WHERE player_id = %s;
            ) AND
            Items.consumable_id IS NOT NULL AND
            type in ('damage', 'heal');'''
        self.cur.execute(query, (player_id,))
        return self.cur.fetchall()
         
    def fetch_combat_items(self, player_id):
        '''Returns two lists of CombatItem objects, damaging & healing, for use in Combat'''
        damaging: list[GameObjects.CombatItem] = []
        healing: list[GameObjects.CombatItem] = []
        for row in self._fetch_combat_items_query(player_id):
            item = GameObjects.CombatItem(row[1], row[2], row[3], range(row[4], row[5]), range(row[6], row[7]), range(row[8], row[9]))
            if row[0] == 'damage':
                damaging.append(item)
            else:
                healing.append(item)
        return damaging, healing



























# def update(self):
#     '''Update the DB with the new player data'''
#     query = '''UPDATE player
#     SET health = %s,
#         coins = %s,
#         energy = %s,
#         knowledge = %s,
#         upgrade_points = %s,
#         experience = %s,
#         level = %s,
#         realm = %s
#     WHERE userid = %s;'''
#     self.cur.execute(query, (
#         self.health,
#         self.coins,
#         self.energy,
#         self.knowledge,
#         self.upgrade_points,
#         self.experience,
#         self.level,
#         self.realm,
#         self.player_id
#     ))

# def delete(self):
#     '''Deletes the player from the DB'''
#     query = '''DELETE FROM player
#     WHERE userid = %s;'''
#     self.cur.execute(query, (self.player_id))


# def fetch_base_item_data(self, id: int = None, name: str = None):
#     '''Query the DB for an item and load it into an item object'''
#     if not id and not name:
#         raise TypeError('{id} or {name} MUST be passed to locate the item')
#     item = Querier.Item()
#     item.id = id
#     item.name = name
#     preq = 'id'
#     if self.name:
#         preq = 'name'

#     query = f'''SELECT *
#     FROM Items
#     WHERE '''+ preq +''' = %s;
#     -- OR
#     WHERE name = $name'''
#     self.cur.execute(query, (self.id if self.id else self.name))
#     return self.cur.fetchone()

