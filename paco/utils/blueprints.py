from flask import Blueprint

paco_bp = Blueprint(
    "paco", __name__, url_prefix="/graphs"
)