import sqlite3
import argparse


parser = argparse.ArgumentParser(description="This program is the final \
stage of Food Blog Backend.")
parser.add_argument("database")
parser.add_argument("--ingredients")
parser.add_argument("--meals")
args = parser.parse_args()
conn = sqlite3.connect(args.database)
food = conn.cursor()
food.execute("""PRAGMA foreign_keys = ON;""")
data = {"meals": ("breakfast", "brunch", "lunch", "supper"),
        "ingredients": ("milk", "cacao", "strawberry", "blueberry", "blackberry", "sugar"),
        "measures": ("ml", "g", "l", "cup", "tbsp", "tsp", "dsp", "")}


def create_database():
    """ Create the initial database as the stage requested."""
    food.execute("""CREATE TABLE IF NOT EXISTS recipes (
                    recipe_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    recipe_name TEXT NOT NULL, 
                    recipe_description TEXT);""")

    food.execute("""CREATE TABLE IF NOT EXISTS meals (
                    meal_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    meal_name TEXT UNIQUE NOT NULL);""")

    food.execute("""CREATE TABLE IF NOT EXISTS ingredients (
                    ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    ingredient_name TEXT UNIQUE NOT NULL);""")

    food.execute("""CREATE TABLE IF NOT EXISTS measures (
                    measure_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    measure_name TEXT UNIQUE);""")

    food.execute("""CREATE TABLE IF NOT EXISTS serve(
                    serve_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meal_id INTEGER NOT NULL,
                    recipe_id INTEGER NOT NULL,
                    FOREIGN KEY(meal_id) REFERENCES meals(meal_id),
                    FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id));""")

    food.execute("""CREATE TABLE IF NOT EXISTS quantity(
                    quantity_id    INTEGER     PRIMARY KEY AUTOINCREMENT,
                    quantity       INTEGER     NOT NULL,
                    recipe_id      INTEGER     NOT NULL,
                    measure_id     INTEGER     NOT NULL,
                    ingredient_id  INTEGER     NOT NULL,
                    FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id),
                    FOREIGN KEY(measure_id) REFERENCES measures(measure_id),
                    FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id)
                    );""")


create_database()


def initializing_database():
    """Insert the requested data."""
    with conn:
        for i in data["meals"]:
            food.execute(f"INSERT OR IGNORE INTO meals (meal_name) VALUES ('{i}');")
        for i in data["ingredients"]:
            food.execute(f"INSERT OR IGNORE INTO ingredients (ingredient_name) VALUES ('{i}');")
        for i in data["measures"]:
            food.execute(f"INSERT OR IGNORE INTO measures (measure_name) VALUES ('{i}');")
        conn.commit()


initializing_database()


meal_result = food.execute(f"SELECT * FROM meals;")
meal_all_rows = meal_result.fetchall()
ingredients_result = food.execute(f"SELECT * FROM ingredients;")
ingredients_all_rows = ingredients_result.fetchall()
measures_result = food.execute(f"SELECT * FROM measures;")
measures_all_rows = measures_result.fetchall()


if args.ingredients and args.meals:
    input_1 = [i for i in args.ingredients.split(",")]  # ["sugar", "milk"]
    input_2 = [i for i in args.meals.split(",")]  # ["breakfast", "brunch"]
    recipe_picked_1, recipe_picked_2 = [], []
    for i in input_1:
        temp_result = food.execute(f"""
                                       SELECT recipe_id
                                       FROM   quantity
                                       WHERE  ingredient_id in 
                                                                (SELECT  ingredient_id
                                                                 FROM    ingredients
                                                                 WHERE   ingredient_name = '{i}')
                                                                ;""").fetchall()
        recipe_picked_1.append(set(temp_result))
    recipe_picked_1 = set.intersection(*recipe_picked_1)

    for i in input_2:
        temp_result = food.execute(f"""
                                       SELECT recipe_id
                                       FROM serve
                                       WHERE meal_id in (
                                                        SELECT meal_id
                                                        FROM meals
                                                        WHERE meal_name = '{i}'
                                                        );""").fetchall()
        recipe_picked_2.append(set(temp_result))

    recipe_picked_2 = set.union(*recipe_picked_2)

    final_result = list(set(recipe_picked_1) & set(recipe_picked_2))
    final_result = [i[0] for i in final_result]
    final_query_string = '''SELECT recipe_name
                    FROM recipes
                    WHERE recipe_id ='''

    really_final = []
    for i in final_result:
        our_recipe = food.execute(f'''{final_query_string} {i}''').fetchall()[0]
        if our_recipe:
            really_final.append(our_recipe)

    really_final = [i[0] for i in really_final]
    if really_final:
        print(f"Recipes selected for you: {', '.join(really_final)}")
    else:
        print("There are no such recipes in the database.")


else:
    print("Pass the empty recipe name to exit.")
    input_recipe = input("Recipe name: ")
    while input_recipe:
        input_description = input("Recipe description: ")
        with conn:
            food.execute(f"""INSERT OR IGNORE INTO recipes (
                            recipe_name, recipe_description) VALUES 
                            ('{input_recipe}', '{input_description}');""")
            conn.commit()

        for i in meal_all_rows:
            print(f"{i[0]}) {i[1]}", end=" ")
        meal_id = input("Enter proposed meals separated by a space: ").split()
        meal_id = [int(i) if i.isnumeric() else i for i in meal_id]  # for example: 1 3 4
        recipe_result = food.execute("""SELECT * FROM recipes""")
        recipe_id = [recipe_result.lastrowid for i in range(len(meal_id))]
        with conn:
            for i in zip(meal_id, recipe_id):
                food.execute('INSERT OR IGNORE INTO serve (meal_id, recipe_id) VALUES (?, ?)', (i[0], i[1]))

        ingredient_enquiry = input("Input quantity of ingredient <press enter to stop>: ").split()
        while ingredient_enquiry:
            ingredient_enquiry = [int(i) if i.isnumeric() else i for i in ingredient_enquiry]
            if len(ingredient_enquiry) == 3:
                q = int(ingredient_enquiry[0])
                m = ingredient_enquiry[1]
                i = ingredient_enquiry[-1]
                if m not in data["measures"]:
                    print("The measure is not conclusive!")
                    ingredient_enquiry = input("Input quantity of ingredient <press enter to stop>: ").split()
            else:
                q = int(ingredient_enquiry[0])
                m = ""
                i = ingredient_enquiry[-1]

            recipe_id = food.execute(f"""SELECT recipe_id 
                                         FROM       recipes 
                                         WHERE      recipe_name = ('{input_recipe}');""").fetchall()[-1][0]
            measures_id = food.execute(f"""SELECT   measure_id 
                                           FROM     measures 
                                           WHERE    measure_name = ('{m}')""").fetchone()[0]
            with conn:
                food.execute(f"""INSERT OR IGNORE INTO ingredients
                                 (ingredient_name) VALUES ('{i}');""")
                ingredients_id = food.execute('''SELECT ingredient_id FROM ingredients WHERE ingredient_name = (?)''', (i,)).fetchone()[0]
                food.execute(f"""INSERT OR IGNORE INTO quantity 
                                 (quantity, recipe_id,   measure_id,    ingredient_id) VALUES 
                                 ('{q}',   {recipe_id}, {measures_id}, {ingredients_id})""")
                conn.commit()
            ingredient_enquiry = input("Input quantity of ingredient <press enter to stop>: ").split()

        print("Pass the empty recipe name to exit.")
        input_recipe = input("Recipe name: ")

conn.close()
