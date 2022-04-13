from dotenv import load_dotenv
from menu import MainMenu
from os import getenv
import psycopg2

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

        print('PostgreSQL connection opened...')
        MainMenu(connection, cursor)

    except (Exception, psycopg2.Error) as error:
        print(f"Error: {type(error).__name__}", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print('\nPostgreSQL connection closed.')