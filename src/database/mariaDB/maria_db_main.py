import os
import mariadb
import sys

# Globale Variable, die die Verbindung mit der Datenbank darstellt
conn = None

'''
    Verbindungsgerstellung mit MariaDB
'''


def init_database():
    try:
        global conn
        conn = mariadb.connect(
            user=os.environ['MARIADB_USER'],
            password=os.environ['MARIADB_PASS'],
            host=os.environ['MARIADB_HOST'],
            port=int(os.environ['MARIADB_PORT']),
            database=os.environ['MARIADB_NAME'],
        )
        print("Debug: Database connection established")
        return True
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)


def get_something_from_database():
    if conn is None:
        return

    cur = conn.cursor()
    cur.execute("SELECT * FROM EVENT_LOG WHERE 1")
    try:
        something = next(cur)[0]
        return something
    except StopIteration:
        return "Failed"
