from flask import Flask
#from flask_cors import CORS
from databases.mariadb_services import mariadb_service as mariadb
from databases.mongodb_services import mongodb_service as mongodb
from waitress import serve

def create_app():

    from .configs.blueprints import paco_bp

    # create and configure the app
    paco_app = Flask(__name__, instance_relative_config=True)
    serve(app, port=8080)
    #CORS(paco, resources={r"/notification-service/*": {"origins": "*"}})

    mariadb.init_database()  # Connect to MariaDB
    mongodb.init_database()  # Connect to MongoDB
    paco_app.run()

    with paco_app.app_context():
        paco_app.register_blueprint(paco_bp)

    return paco_app
