from flask import Flask
from dotenv import load_dotenv
from flasgger import Swagger
from flask_migrate import Migrate
from flask_cors import CORS

from admin.database import db

from config import BANK_DATABASE_URI
from admin.statements_hdfc import hdfc_bp
from admin.statements_icici import icici_bp
from admin.statements_sbi import sbi_bp

app = Flask(__name__)
swagger = Swagger(app)
CORS(app)

# Register the Blueprint
app.register_blueprint(sbi_bp)
app.register_blueprint(icici_bp)
app.register_blueprint(hdfc_bp)


app.config['SQLALCHEMY_DATABASE_URI'] = BANK_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    return 'Bank Statments V.02'

