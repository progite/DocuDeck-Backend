import uuid
from flask import Flask, request, jsonify, send_from_directory, make_response
# from flaskext.mysql import MySQL
from flask_mysqldb import MySQL
import database as database
import os, datetime
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from helper_utils import extract_date

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = str(uuid.uuid4())
jwt = JWTManager(app)

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'DocuDeck'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql = MySQL(app)
with app.app_context():
    policy_db = database.PolicyDB(mysql) #is this accessible outside this segement
    tender_db = database.TenderDB(mysql)

if __name__ == "-__main__":
    app.run()

@app.route("/add-policy", methods = ["PUT"])
# @jwt_required()
def add_report_to_db():
    # current_user = get_jwt_identity()
    # user_account_type = get_jwt()['Account Type']

    #extract policy uploader id from jwt token
    content = request.get_json()
    policy_id = content['policy_id']
    date = content['date']
    date = extract_date(date)
    policy = content['policy']
    pmId = 1
    with app.app_context():
        policy_db.add_policy(policy_id, date, policy, pmId)
    print("[DEBUG], ENTERED HERE")
            
    return "ok", 200

@app.route("/search-policies", methods= ['GET'])
def search_policies():
    content = request.get_json()
    #TODO: consider tags too
    policy_id = content['policy_id']
    date = extract_date(content['issue_date'])
    date_from = content['date_from']
    date_from = datetime.date.min if date_from == "" else extract_date(date_from)
    date_to = content['date_to']
    date_to = datetime.date.max if date_to == "" else extract_date(date_to)
    dept = content['department']
    ministry = content['ministry']

    with app.app_context():
        policy_db.search_policies(policy_id, date, date_from, date_to, dept, ministry)
    return "ok", 200