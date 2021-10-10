from flask import Flask, jsonify
# from flask_cors import CORS
import time
from src.database.mariaDB import maria_db_main as maria_db
from src.database.mongoDB import mongo_db_main as mongo_db

app = Flask(__name__)
# CORS(app, resources={r"/api-py/*": {"origins": "*"}})


@app.route('/api/')
def calculate_new_graph():  # put application's code here
    start = time.time()
    maria_db.init_database() # Connect to MariaDB
    response_message = maria_db.get_something_from_database()
    mongo_db.init_database()  # Connect to MariaDB
    response_message2 = mongo_db.get_something_from_database()
    # response_message = calculateGraph()
    dict = {"text1": response_message, "text2": response_message2}
    response = jsonify(dict)
    response.status_code = 200
    end = time.time()
    request_duration = (end - start)
    print(f"Reponse: {response}")
    print(f"\n<--- Execute-Duration: {request_duration} --->")
    # response.headers.add("Access-Control-Allow-Origin", "*")
    return response


if __name__ == '__main__':
    app.run()
