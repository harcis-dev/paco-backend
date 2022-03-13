from waitress import serve
from configs.blueprints import paco_bp
serve(paco_bp, host='0.0.0.0', port=5000)