import os
import mariadb
import sys

# Global variable with connection to MariaDB
from src.configs import config
from src.eventlog.sapeventlog import Filter
from src.model.event import Event

conn = None

'''
    Connection establishment and queries to MariaDB 
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


''' SAP EVENT LOG '''

'''
    Returns a set of ids of all available sequences in the database
'''
def all_sequences():
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
        return "Failed"

'''
    Returns a list of events for the sequence sid with attributes
    "concept_name", "alt_concept_name", "lifecycle_transition", "org_resource", "time_timestamp", "transaction"
'''
def events(sid):
    if conn is None:
        init_database()

    cur = conn.cursor()
    cur.execute(
        "SELECT D.TTEXT AS concept_name, S.BLART AS alt_concept_name, 'complete' AS lifecycle_transition, "
        "USNAM AS org_resource, CONCAT(CPUDT, ' ', CPUTM) AS time_timestamp, TSTCT.TTEXT AS transaction FROM SEQUENCE S "
        f"LEFT JOIN DOCTYPE D ON (S.BLART=D.BLART) AND D.SPRSL='{config.language}'"
        f"LEFT JOIN TSTCT ON (S.TCODE=TSTCT.TCODE) AND TSTCT.SPRSL='{config.language}'"
        f"WHERE SEQUENCEID='{sid}' ORDER BY POS")
    try:
        events = []
        for (concept_name, alt_concept_name, lifecycle_transition, org_resource, time_timestamp, transaction) in cur:
            e_name = concept_name if concept_name is not None else alt_concept_name
            e = Event(e_name)
            e.attributes = {"lifecycle_transition": lifecycle_transition, "org_resource": org_resource,
                            "time_timestamp": time_timestamp, "transaction": transaction}
            events.append(e)

        return events
    except StopIteration:
        return "Failed"

'''
    Returns sequences ids for the given filter and its values (e.g. creditor and creditor id-numbers)
'''
def filter_sequences(filter, values):
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
        return "Failed"
