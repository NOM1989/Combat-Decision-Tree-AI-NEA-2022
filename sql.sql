-- Player Data (not inv data)
CREATE TABLE IF NOT EXISTS Players (
    player_id BIGINT PRIMARY KEY,
    name VARCHAR NOT NULL,
    max_health SMALLINT DEFAULT 10,
    coins INT DEFAULT 1000,
    energy SMALLINT DEFAULT 0,
    experience INT DEFAULT 0,
);

-- Player Queries
-- Create Player
INSERT INTO player(player_id)
VALUES ($player_id)
RETURNING *;
-- Check what returns -> OID? count attribute is number of rows inserted

-- Select player
SELECT name, max_health, coins, energy, experience
FROM Players
WHERE player_id = $player_id;
-- OR
SELECT health, coins, energy, knowledge, upgrade_points, experience, level, realm
FROM Players
WHERE player_id = $player_id;

-- Delete Player
DELETE FROM Players
WHERE player_id = $player_id;
-- Returns number of rows deleted

-- Update Player
UPDATE player
SET health = $health,
    coins = $coins,
    energy = $energy,
    knowledge = $knowledge,
    upgrade_points = $upgrade_points,
    experience = $experience,
    level = $level,
    realm = $realm
WHERE player_id = $player_id;


-- Used to store player items
CREATE TABLE IF NOT EXISTS PlayerItems (
    player_id BIGINT NOT NULL,
    item_id SMALLINT NOT NULL,
    quantity SMALLINT DEFAULT 1 NOT NULL,
    PRIMARY KEY(player_id, item_id)
);

-- Remove items from player inv
UPDATE PlayerItems
SET quantity = $amount
WHERE player_id = $player_id AND
id = $item_id;

DELETE FROM PlayerItems
WHERE player_id = $player_id AND
id = $item_id;


-- Get a players inv
SELECT id, quantity
FROM PlayerItems
WHERE player_id = $player_id;
-- OR
SELECT quantity
FROM PlayerItems
WHERE player_id = $player_id AND
    id = $item_id;
-- 

-- Select item with consumable data and join
SELECT type, Items.item_id, name, quantity, min_range, max_range, min_turns, max_turns, min_experience, max_experience
FROM Items
INNER JOIN PlayerItems ON Items.item_id = PlayerItems.item_id
INNER JOIN ConsumableData ON Items.consumable_id = ConsumableData.consumable_id
WHERE Items.item_id IN (
    SELECT PlayerItems.item_id
    FROM PlayerItems
    WHERE player_id = $player_id;
) AND
Items.consumable_id IS NOT NULL AND
type IN ('damage', 'heal');


-- Update item in players inv
UPDATE PlayerItems
    SET quantity = quantity + $amount
WHERE player_id = $player_id AND
    id = $item_id
RETURNING quantity;

-- Add an item to players inv
INSERT INTO PlayerItems
VALUES ($player_id, $id, $quantity);


-- Sequence to keep track of the next recipe_id
CREATE SEQUENCE IF NOT EXISTS RecipesRecipeIdSequence;

CREATE TABLE IF NOT EXISTS Recipes (
    recipe_id SMALLINT NOT NULL,
    item_id SMALLINT NOT NULL,
    quantity SMALLINT DEFAULT 1 NOT NULL,
    PRIMARY KEY (recipe_id, item_id)
);

-- Tether sequence to id column so if we end up deleting the column it gets removed too
ALTER SEQUENCE RecipesRecipeIdSequence OWNED BY Recipes.recipe_id;

-- To add a new recipie, query nextval then add all the ingredients and quantities with the returned id
SELECT NEXTVAL('RecipesRecipeIdSequence');

-- Add ingredient to recipe
INSERT INTO recipes
VALUES ($recipe_id, $ingredient_id, $quantity);

-- Add recipe_id to item
UPDATE Items
SET recipe_id = $recipe_id
WHERE id = $item_id;

CREATE TABLE IF NOT EXISTS ConsumableData (
    consumable_id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    type VARCHAR NOT NULL,
    min_range SMALLINT,
    max_range SMALLINT,
    min_experience SMALLINT,
    max_experience SMALLINT,
    min_turns SMALLINT,
    max_turns SMALLINT,
    CONSTRAINT if_min_range_then_check_max_range_greater_or_equal CHECK ( (NOT min_range) OR (max_range >= min_range) ),
    CONSTRAINT if_min_experience_then_check_max_experience_greater_or_equal CHECK ( (NOT min_experience) OR (max_experience >= min_experience) ),
    CONSTRAINT if_min_turns_then_check_max_turns_greater_or_equal CHECK ( (NOT min_turns) OR (max_turns >= min_turns) )
);

-- How I will store game things (Spells, Potions, Items, Resources)
CREATE TABLE IF NOT EXISTS Items (
    item_id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR NOT NULL,
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
);


-- Get all item names and ids
SELECT id, name
FROM Items;

-- Select things data
SELECT *
FROM Items
WHERE id = $id
-- OR
WHERE name = $name

-- Select consumable data
SELECT *
FROM ConsumableData
WHERE id = $consumable_id


-- Simplified query (missing fields) for Inserting a game thing with no consumable data
INSERT INTO Items(name, description, category, emoji, value, level, rarity)
    VALUES ($name, $description, $category, $emoji, $value, $level, $rarity);

INSERT INTO ConsumableData(type, min_range, max_range, min_experience, max_experience, min_turns, max_turns)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING id;

UPDATE Items
    SET consumable_id = $consumable_id
    WHERE id = $item_id;
-- 



-- ALL BELOW IS BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD
-- BAD

-- Old add item with consumable data
WITH rows (id) AS (
  INSERT INTO ConsumableData(type, min_range, max_range, min_experience, max_experience, min_turns, max_turns)
  VALUES ($type, $min_range, $max_range, $min_experience, $max_experience, $min_turns, $max_turns)
  RETURNING id
)
INSERT INTO Items (name, description, category, emoji, value, level, rarity, consumable_id)
  VALUES ($name, $description, $category, $emoji, $value, $level, $rarity, id)
;






CREATE TABLE IF NOT EXISTS things (
    
);

CREATE TABLE IF NOT EXISTS things_recipes (
    
);

-- Each category will have their own table (Spells, Potions)
CREATE TABLE IF NOT EXISTS spells_data (
    id SMALLINT PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR,
    emoji VARCHAR,
    value SMALLINT NOT NULL,
    level SMALLINT NOT NULL,
    rarity VARCHAR NOT NULL CONSTRAINT valid_rarity CHECK (rarity in ('legendary', 'mythical', 'epic', 'rare', 'uncommon', 'common')),
    type VARCHAR NOT NULL,
    recipe_id SMALLINT,
    min_range SMALLINT,
    max_range SMALLINT,
    min_xp SMALLINT,
    max_xp SMALLINT,
    min_turns SMALLINT,
    max_turns SMALLINT,

    CONSTRAINT if_min_range_then_check_max_range_greater_or_equal CHECK ( (NOT min_range) OR (max_range >= min_range) ),
    CONSTRAINT if_min_xp_then_check_max_xp_greater_or_equal CHECK ( (NOT min_xp) OR (max_xp >= min_xp) ),
    CONSTRAINT if_min_turns_then_check_max_turns_greater_or_equal CHECK ( (NOT min_turns) OR (max_turns >= min_turns) )
    -- Research time can be calculated from value
);

-- WORK OUT HOW GOING TO DO FOUND IN - Done

-- Each category will have their own table
CREATE TABLE IF NOT EXISTS items_data (
    id SMALLINT PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR,
    emoji VARCHAR,
    value SMALLINT NOT NULL,
    level SMALLINT NOT NULL,
    rarity VARCHAR NOT NULL CONSTRAINT valid_rarity CHECK (rarity in ('legendary', 'mythical', 'epic', 'rare', 'uncommon', 'common')),
    type VARCHAR NOT NULL,
    recipe_id SMALLINT,
    min_range SMALLINT,
    max_range SMALLINT,
    min_xp SMALLINT,
    max_xp SMALLINT,
    min_turns SMALLINT,
    max_turns SMALLINT,

    CONSTRAINT if_min_range_then_check_max_range_greater_or_equal CHECK ( (NOT min_range) OR (max_range >= min_range) ),
    CONSTRAINT if_min_xp_then_check_max_xp_greater_or_equal CHECK ( (NOT min_xp) OR (max_xp >= min_xp) ),
    CONSTRAINT if_min_turns_then_check_max_turns_greater_or_equal CHECK ( (NOT min_turns) OR (max_turns >= min_turns) )
    -- Research time can be calculated from value
);

CREATE TABLE IF NOT EXISTS resources_data (
    id SMALLINT PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR,
    emoji VARCHAR,
    value SMALLINT NOT NULL,
    level SMALLINT NOT NULL,
    rarity VARCHAR NOT NULL CONSTRAINT valid_rarity CHECK (rarity in ('legendary', 'mythical', 'epic', 'rare', 'uncommon', 'common')),
    type VARCHAR NOT NULL,
    recipe_id SMALLINT
);








-- Query all spells a player has
SELECT thing_id, quantity FROM spells WHERE userid = {userid};


-- Query a certain spell
SELECT * FROM spells WHERE id = {spell_id}




CREATE TABLE IF NOT EXISTS realm (
    id SMALLINT NOT NULL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS structure (
    id SMALLINT NOT NULL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS found_in (
    thing_id SMALLINT NOT NULL,
    realm_id SMALLINT NOT NULL,
    structure_id SMALLINT NOT NULL
);