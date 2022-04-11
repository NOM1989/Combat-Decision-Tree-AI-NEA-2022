from dotenv import load_dotenv
from load_csv import Loader
from combat import Combat
from query import Querier
from setup import Setup
from os import getenv
import traceback
import psycopg2

class Main():
    '''Overarching class to run the program'''
    def __init__(self) -> None:
        load_dotenv()
        db_username = getenv('DB_USERNAME')
        db_pass = getenv('DB_PASS')
        db_name = getenv('DB_NAME')
        db_host = getenv('DB_HOST')

        try:
            self.connection = psycopg2.connect(user=db_username,
                                        password=db_pass,
                                        host=db_host,
                                        database=db_name)
            self.connection.set_session(autocommit=True)
            self.cursor = self.connection.cursor()

            self.querier = Querier(self.connection, self.cursor)  # Created an instance of the Querier class to run our DB functions and calls
            
            # Setup(self.connection, self.cursor)
            # Loader(self.querier, self.connection, self.cursor, '~/NEA/data.csv')

            player_id = 0
            # items = [
            #     'sparking',
            #     'blast of bones',
            #     'elemental explosion',
            #     'forest brew'
            # ]
            # for item in items:
            #     self.querier.players.update_item(self.querier.items.name_id_map, player_id, 2, item_name=item)

            Combat(self.querier, player_id)

        except (Exception, psycopg2.Error) as error:
            print(f"Error - {type(error).__name__}", error)
            traceback.print_tb(error.__traceback__)
        finally:
            if self.connection:
                self.cursor.close()
                self.connection.close()
                print("PostgreSQL connection is closed")

Main()