from flask import Flask
# from flask_cors import CORS
from paco.databases.mariadb_services import mariadb_service as mariadb
from paco.databases.mongodb_services import mongodb_service as mongodb


def create_app():
    from paco.utils.blueprints import paco_bp

    # Logging to the file paco-backend/paco/paco_logs/paco_debug.log
    import logging
    import os
    from datetime import datetime
    log_filename = "paco_logs/paco_debug.log"
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    logging.FileHandler(log_filename, mode="w", encoding=None, delay=False)
    logging.basicConfig(filename="paco_logs/paco_debug.log", level=logging.DEBUG)
    logging.debug(str(datetime.now(tz=None)) + " __Init__")
    print("\n\n__init__\n\n")

    # create and configure the app
    paco_app = Flask(__name__, instance_relative_config=True)
    # CORS(paco, resources={r"/notification-service/*": {"origins": "*"}})

    paco_app.run()

    with paco_app.app_context():
        paco_app.register_blueprint(paco_bp)

    return paco_app
