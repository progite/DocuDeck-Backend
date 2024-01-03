import uuid
from flask import Flask, request, jsonify, send_from_directory, make_response
# from flaskext.mysql import MySQL
from flask_mysqldb import MySQL
import database as database
import os, datetime
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from helper_utils import extract_date
from flask_cors import CORS
from constants import USER_1, USER_2, USER_3
import ml_int
import tender_rule_similarity_ml

app = Flask(__name__)
CORS(app)

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'DocuDeck'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql = MySQL(app)
with app.app_context():
    print(mysql)
    policy_db = database.PolicyDB(mysql) #is this accessible outside this segement
    tender_db = database.TenderDB(mysql)

if __name__ == "-__main__":
    app.run()

@app.route("/sign-up", methods= ["PUT"])
def sign_up():
    #email, password, user type
    content = request.get_json()
    user_id = str(uuid.uuid4())
    user_email = content['email']
    user_password = content['password']
    user_type = content['userType']

    if user_type not in [USER_1, USER_2, USER_3]:
        return "Invalid User Type", 400

    status = policy_db.add_user(user_id, user_email, user_password, user_type)
    if status:
        return jsonify("User added successfully"), 200
    return jsonify("User could not be added"), 500

@app.route("/login", methods = ["POST"])
def login():
    content = request.get_json()
    user_email = content['email']
    user_password = content['password']
    user_type = content['userType']

    status = policy_db.login(user_email, user_password, user_type)
    
    if status:
        return jsonify("Login Successful"), 200
    return jsonify("Invalid Credentials"), 400

@app.route("/add-policy", methods = ["PUT"])
def add_policy():
    
    #TODO: add policy uploader id
    if 'policy' in request.files:
        pm_id = request.form['pmId']
        policy = request.files['policy']
        policy_name = policy.filename
        if policy_db.add_policy(pm_id, policy, policy_name):
            return "Policy added to database", 200
        return "Could not add policy", 500
    
    return "Invalid Request", 400
    
@app.route("/search-policies", methods= ['POST'])
def search_policies():
    content = request.get_json()
    #TODO: consider tags too
    policy_id = content['policy_id']
    if policy_id == '':
        policy_id = None
    date = content['issue_date']
    date = None if not date else extract_date(date)
    date_from = content['date_from']
    date_from = datetime.date.min if not date_from else extract_date(date_from)
    date_to = content['date_to']
    date_to = datetime.date.max if not date_to else extract_date(date_to)
    dept = content['department']
    if dept == '':
        dept = None
    ministry = content['ministry']
    if ministry == '':
        ministry = None

    keywords = content['keywords']
    print("[DEBUG] KEYWORDS FETCHED", keywords)
    with app.app_context():
        policies_list = policy_db.search_policies(policy_id, date, date_from, date_to, dept, ministry, keywords)
    
    if policies_list:
        return jsonify(policies_list), 200
    return "Details could not be fetched", 500 #server side error

@app.route("/add-tender", methods=['POST'])
def add_tender():
    if 'tender' in request.files:
        #this will be uploaded 
        # tender_id = request.form['tenderId'] #make tender reference number into this 
        tender_id = str(uuid.uuid4())
        ta_id = request.form['taId']
        tender = request.files['tender']
        tender_name = tender.filename
        status = tender_db.add_tender(tender_id, ta_id, tender_name, tender)
        if status:
            return jsonify(status), 200
        return "Could not add tender", 500
    
    return "Invalid Request", 400
    
#fetch all tenders/for one user
@app.route("/fetch-tenders", methods= ['GET'])
def fetch_tendors():
    ta_id = request.args.get('taId') #has to be NULL if it is not to be provided
    ta_id = ta_id if ta_id else None
    tenders_list = tender_db.fetch_tenders(ta_id)
    return jsonify(tenders_list), 200

@app.route("/add-bid", methods=['POST'])
def add_bid():
    #multiple files can be there
    file_list = list()
    file_names = list()
    for file in request.files.getlist('file'):
        file_list.append(file)      
        file_names.append(file.filename)
    
    vid = request.form['vId']
    tender_id = request.form['tenderId']

    status = tender_db.add_bid(vid, tender_id, file_list, file_names)
    if status:
        return jsonify("Bid Added Successfully"), 200
    
    return jsonify("Could not add bid"), 500

@app.route("/add-bid-docs", methods=['POST'])
def add_bid_docs():
    if 'docs' in request.files:
        docs_list = request.files.getlist('docs')
        status = tender_db.bid_documents_check(docs_list)
        if status:
            return jsonify(status), 200
        return jsonify("Could not process document"), 500
        # print(docs_list, "DEBUGGGGG")
    return jsonify("Invalid Docs Uploaded"), 400

@app.route("/fetch-bid", methods=["GET"])
def fetch_bid():
    tender_id = request.args.get('tenderId')
    status = tender_db.fetch_bid(tender_id)
    
    return jsonify(status), 200 if status else 500

@app.route("/bid-chatbot", methods=["GET"])
def bid_chatbot():
    question = request.args.get("question")
    tender_id = request.args.get("tenderId")
    print(question, tender_id)
    response = tender_db.bid_chatbot(question, tender_id)
    if response:
        return jsonify(response), 200
    return "Could not fetch response", 500

@app.route("/publish-tender", methods=["POST"])
def publish_tender():
    if 'tender' in request.files:
        tender_id = str(uuid.uuid4())
        ta_id = request.form['taId']
        date = request.form['date'] #today's date because if a new tender is being uploaded, it's on that date
        tender = request.files['tender']
        print("ENTERS HEREEE")
        
        tender_name = tender.filename
        status = tender_db.publish_tender(tender_id, ta_id, tender_name, date, tender)
        if status:
            return jsonify(status), 200
        return "Could not add tender", 500
    
#tenders against bidders which bidder has bidded for that tender
#against each tender, bidder and their uploaded docs

#Bidders upload documents-against tender

#1 db for tender-bidder mapping (1 endpoint)
#bidder max docs upload - 5
