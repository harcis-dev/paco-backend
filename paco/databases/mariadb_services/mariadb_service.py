import os
import mariadb
import sys

# Global variable with connection to MariaDB
from ...configs import configs as ct
from ...model.event import Event

conn = None

'''
    Connection establishment and queries to MariaDB 
'''

'''
user=os.environ.get('MARIADB_USER'),
password=os.environ.get('MARIADB_PASS'),
host=os.environ.get('MARIADB_HOST'),
port=os.environ.get('MARIADB_PORT'),
database=os.environ.get('MARIADB_NAME'),
'''
def init_database():
    try:
        global conn
        conn = mariadb.connect(
            user="root",
            password="123456",
            host="127.0.0.1",
            port=8991,
            database="sap",
        )
        print("Debug: Database connection established")
        return True
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)


def get_something_from_database():
    if conn is None:  # retry
        init_database()  # sys.exit if no connection could be established

    cur = conn.cursor()
    cur.execute("SELECT * FROM SOMETABLE WHERE 1")
    try:
        something = next(cur)[0]
        return something
    except StopIteration:
        return "Failed"


''' SAPDATA '''

'''
    Returns a set of ids of all available cases in the database
'''


def all_cases():
    if conn is None:
        init_database()

    cur = conn.cursor()
    cur.execute("SELECT DISTINCT SEQUENCEID FROM SEQUENCE")
    res = set()
    try:
        for sid in cur:
            res.add(sid[0])
        return res
    except StopIteration:
        return "Empty"


'''
    Returns a list of events for the case sid with attributes
    "concept_name", "alt_concept_name", "lifecycle_transition", "org_resource", "time_timestamp", "transaction"
'''


def events(cid):
    if conn is None:
        init_database()

    cur = conn.cursor()
    cur.execute(
        "SELECT D.TTEXT AS concept_name, S.BLART AS alt_concept_name, 'complete' AS lifecycle_transition, "
        "USNAM AS org_resource, CONCAT(CPUDT, ' ', CPUTM) AS time_timestamp, TSTCT.TTEXT AS transaction FROM SEQUENCE S "
        f"LEFT JOIN DOCTYPE D ON (S.BLART=D.BLART) AND D.SPRSL= BINARY '{ct.Configs.LANGUAGE}'"
        f"LEFT JOIN TSTCT ON (S.TCODE=TSTCT.TCODE) AND TSTCT.SPRSL= BINARY '{ct.Configs.LANGUAGE}'"
        f"WHERE SEQUENCEID='{cid}' ORDER BY POS")
    try:
        events = []
        for idx, (concept_name, alt_concept_name, lifecycle_transition, org_resource, time_timestamp, transaction) in enumerate(cur):
            e_name = concept_name if concept_name is not None else alt_concept_name
            e = Event(f"{e_name.replace(' ', '_')}_{cid}_{idx}", e_name)
            e.attributes = {"lifecycle_transition": lifecycle_transition, "org_resource": org_resource,
                            "time_timestamp": time_timestamp, "transaction": transaction}
            events.append(e)

        return events
    except StopIteration:
        return "Not Found"


def functions(cid):
    if conn is None:
        init_database()

    cur = conn.cursor()
    cur.execute(
        f"SELECT TCODE AS concept_name, 'complete' AS lifecycle_transition, USNAM AS org_resource, CONCAT(CPUDT, ' ', CPUTM) AS time_timestamp FROM SEQUENCE WHERE SEQUENCEID = '{cid}' ORDER BY POS")
    try:
        tcode = next(cur)[0]
        return tcode
    except StopIteration:
        return "Not Found"

'''
    Returns cases ids for the given filter and its values (e.g. creditor and creditor id-numbers)
'''


def filter_cases(filter, values):
    if conn is None:
        init_database()

    stmt = "SELECT DISTINCT SEQUENCEID FROM SEQUENCE S" \
           "JOIN BSEG B ON (S.MANDT=B.MANDT AND S.BUKRS=B.BUKRS AND S.GJAHR=B.GJAHR AND S.BELNR=B.BELNR)" \
           "WHERE "

    for val in values:
        stmt += f"{filter}='{val}' OR "

    cur = conn.cursor()
    cur.execute(stmt[:-4])  # remove the last " OR "
    res = set()
    try:
        for sid in cur:
            res.add(sid[0])
        return res
    except StopIteration:
        return "Not Found"
