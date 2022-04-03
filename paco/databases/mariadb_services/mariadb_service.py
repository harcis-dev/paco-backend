import os
import mariadb
import sys

from mariadb import ProgrammingError

import paco.app
from paco.utils import configs as ct, utils
from paco.model.event import Event

# A global variable with connection to MariaDB
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
        print("MariaDB: Database connection established")
        return True
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)


init_database()  # Connect to MariaDB


""" SAPDATA """

'''
    Returns a set of ids of all available cases in the database
'''


def all_cases():
    if conn is None:
        init_database()

    cur = conn.cursor()

    try:
        cur.execute("SELECT DISTINCT SEQUENCEID FROM SEQUENCE")
    except ProgrammingError as pe:
        utils.print_error(pe)
        ct.Errcodes.curr_errcode = ct.Errcodes.MARIADB_NO_DATA
        return None

    res = set()
    try:
        for sid in cur:
            res.add(sid[0])
        return res
    except StopIteration:
        ct.Errcodes.curr_errcode = ct.Errcodes.MARIADB_NO_DATA
        return None


'''
    Returns a list of events for the case sid with attributes
    "concept_name", "alt_concept_name", "lifecycle_transition", "org_resource", "time_timestamp", "transaction"
'''


def events(cid):
    if conn is None:
        init_database()

    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT D.TTEXT AS concept_name, S.BLART AS alt_concept_name, 'complete' AS lifecycle_transition, "
            "USNAM AS org_resource, CONCAT(CPUDT, ' ', CPUTM) AS time_timestamp, TSTCT.TTEXT AS transaction FROM SEQUENCE S "
            f"LEFT JOIN DOCTYPE D ON (S.BLART=D.BLART) AND D.SPRSL= BINARY '{ct.Configs.LANGUAGE}'"
            f"LEFT JOIN TSTCT ON (S.TCODE=TSTCT.TCODE) AND TSTCT.SPRSL= BINARY '{ct.Configs.LANGUAGE}'"
            f"WHERE SEQUENCEID='{cid}' ORDER BY POS")
    except ProgrammingError as pe:
        utils.print_error(pe)
        ct.Errcodes.curr_errcode = ct.Errcodes.MARIADB_NO_DATA
        return None

    try:
        events = []
        for idx, (
                concept_name, alt_concept_name, lifecycle_transition, org_resource, time_timestamp,
                transaction) in enumerate(
            cur):
            e_name = concept_name if concept_name is not None else alt_concept_name
            e = Event(f"{e_name.replace(' ', '_')}_{cid}_{idx}", e_name)
            e.attributes = {"lifecycle_transition": lifecycle_transition, "org_resource": org_resource,
                            "time_timestamp": time_timestamp, "transaction": transaction}
            events.append(e)

        return events
    except StopIteration:
        ct.Errcodes.curr_errcode = ct.Errcodes.MARIADB_NO_DATA
        return None


def functions(cid):
    if conn is None:
        init_database()

    cur = conn.cursor()

    try:
        cur.execute(
            f"SELECT TCODE AS concept_name, 'complete' AS lifecycle_transition, USNAM AS org_resource, CONCAT(CPUDT, ' ', CPUTM) AS time_timestamp FROM SEQUENCE WHERE SEQUENCEID = '{cid}' ORDER BY POS")
    except ProgrammingError as pe:
        utils.print_error(pe)
        ct.Errcodes.curr_errcode = ct.Errcodes.MARIADB_NO_DATA
        return None

    try:
        tcode = next(cur)[0]
        return tcode
    except StopIteration:
        ct.Errcodes.curr_errcode = ct.Errcodes.MARIADB_NO_DATA
        return None


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

    try:
        cur.execute(stmt[:-4])  # remove the last " OR "
    except ProgrammingError as pe:
        utils.print_error(pe)
        ct.Errcodes.curr_errcode = ct.Errcodes.MARIADB_NO_DATA
        return None

    res = set()
    try:
        for sid in cur:
            res.add(sid[0])
        return res
    except StopIteration:
        ct.Errcodes.curr_errcode = ct.Errcodes.MARIADB_NO_DATA
        return None
