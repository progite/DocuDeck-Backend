import uuid
from flask import Flask, request, jsonify, send_from_directory, make_response
# from flaskext.mysql import MySQL
from flask_mysqldb import MySQL
import database as database
import os, datetime
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from helper_utils import extract_date
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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
def add_policy_to_db():
    
    content = request.get_json()
    # policy_id = content['policy_id']
    # date = content['date']
    # date = extract_date(date)
    policy_id = 1
    date = extract_date("2023-10-10")
    policy = content['policy']
    pmId = 1
    with app.app_context():
        policy_db.add_policy(policy_id, date, policy, pmId)
    print("[DEBUG], ENTERED HERE")
            
    return "ok", 200

@app.route("/search-policies", methods= ['POST'])
def search_policies():
    content = request.get_json()
    #TODO: consider tags too
    policy_id = content['policy_id']
    date = content['issue_date']
    date = None if not date else extract_date(date)
    date_from = content['date_from']
    date_from = datetime.date.min if not date_from else extract_date(date_from)
    date_to = content['date_to']
    date_to = datetime.date.max if not date_to else extract_date(date_to)
    dept = content['department']
    ministry = content['ministry']

    with app.app_context():
        policies_list = policy_db.search_policies(policy_id, date, date_from, date_to, dept, ministry)
    
    if policies_list:
        return jsonify(policies_list), 200
    return "Details could not be fetched", 500 #server side error

#fetch all tenders
@app.route("/fetch-tenders", methods= ['GET'])
def fetch_tendors():
    #takes no arguments
    tenders_list = tender_db.fetch_tenders()
    print("[DEBUG]", tenders_list)
    return jsonify(tenders_list), 200

#fetch tenders for one user 

#compilance check of tender with respective rules 

#tenders against bidders which bidder has bidded for that tender