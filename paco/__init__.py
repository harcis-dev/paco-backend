from flask import Flask


def create_app():
    from paco.utils.blueprints import paco_bp
    from paco import app
    from paco.databases.mariadb_services import mariadb_service
    from paco.databases.mongodb_services import mongodb_service

    # create and configure the app
    paco_app = Flask(__name__, instance_relative_config=True)

    with paco_app.app_context():
        paco_app.register_blueprint(paco_bp)

    mariadb_service.init_database()
    mongodb_service.init_database()

    return paco_app
