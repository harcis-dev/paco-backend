from flask import Flask, jsonify, request
# from flask_cors import CORS
import time
from src.databases.mariadb_services import mariadb_service as mariadb
from src.databases.mongodb_services import mongodb_service as mongodb
from src.eventlog.sapeventlog import SapEventLog

app = Flask(__name__)


# CORS(app, resources={r"/api-py/*": {"origins": "*"}})


@app.route('/new-data')
def calculate_new_graph():  # put application's code here
    start = time.time()

    filters = request.args.getlist('filters')
    se = SapEventLog()
    se.read_data(filters)
    print(se.sequences)

    end = time.time()
    request_duration = (end - start)
    print(f"\n<--- Execution duration: {request_duration} --->")
    # response.headers.add("Access-Control-Allow-Origin", "*")
    return '', 204

if __name__ == '__main__':
    mariadb.init_database()  # Connect to MariaDB
    #mongodb.init_database()  # Connect to MongoDB
    app.run()
