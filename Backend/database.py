#should the tender and rules database be in separate files?
import os
import uuid
from flask_mysqldb import MySQL
from flask import current_app
from password_utils import hash_password, check_password
from constants import USER_1, USER_2, USER_3
import datetime
import tender_rule_similarity_ml
import bidder_doc_check
from helper_utils import extract_date

class PolicyDB:
    def __init__(self, mysql: MySQL) -> None:
        self.mysql = mysql
        cursor = self.mysql.connection.cursor()

        #create ministry 
        try:
            query = '''CREATE TABLE if not exists `MINISTRY`(
                `minId` VARCHAR(100) PRIMARY KEY, 
                `minName` VARCHAR(100))'''
            cursor.execute(query)
        except Exception as e:
            print("[DEBUG]", e)

        #create department under ministry
        try:
            query = '''CREATE TABLE if not exists `DEPARTMENT` (
                `deptId` VARCHAR(100) PRIMARY KEY, 
                `deptName` VARCHAR(100))'''
            cursor.execute(query)
        except Exception as e:
            print(e)

        #map ministry and dept
        try:
            query = '''CREATE TABLE if not exists `MINISTRY_DEPT` (
                `minId` VARCHAR(100), 
                `deptId` VARCHAR(100),
                FOREIGN KEY(`minId`) REFERENCES `MINISTRY`(`minId`),
                FOREIGN KEY(`deptId`) REFERENCES `DEPARTMENT`(`deptId`),
                PRIMARY KEY(`minId`, `deptId`))
                '''
            cursor.execute(query)
        except Exception as e:
            print("[DEBUG]", e)


        #create user db
        try:
            query = '''CREATE TABLE if not exists `POLICYMAKER`(
                `pmId` VARCHAR(100) PRIMARY KEY, 
                `pmName` VARCHAR(50), 
                `pmEmail` VARCHAR(100),
                `password` VARCHAR(100),
                `deptId` VARCHAR(100),
                FOREIGN KEY(`deptId`) REFERENCES `DEPARTMENT`(`deptId`))
                '''
            cursor.execute(query)
        except Exception as e:
            print(e)

        #create tags db
        try:
            query = '''CREATE TABLE if not exists `TAGS` (
                `tagId` VARCHAR(100) PRIMARY KEY, 
                `tag` VARCHAR(50))'''
            cursor.execute(query)
        except Exception as e:
            print(e)

        #create policy db
        #we need to know who it is published by. We don't know which ministries it affects. Can we?
        #don't need ministry id and dept id here since we can get that from policy-maker id
        try:
            query = '''CREATE TABLE if not exists `POLICIES` (
                `policyId` VARCHAR(100) PRIMARY KEY, 
                `date` DATE NOT NULL,
                `policy` VARCHAR(500) NOT NULL,
                `pmId` VARCHAR(100),
                `deptId` VARCHAR(100), 
                `minId` VARCHAR(100),
                FOREIGN KEY(`pmId`) REFERENCES `POLICYMAKER`(`pmId`),
                FOREIGN KEY(`deptId`) REFERENCES `DEPARTMENT`(`deptId`),
                FOREIGN KEY(`minId`) REFERENCES `MINISTRY`(`minId`))
                '''
            cursor.execute(query)
        except Exception as e:
            print("[DEBUG]", e)

        #mapping policies to tags
        try:
            query = '''CREATE TABLE if not exists `POLICY_TAGS` (
                `tagId` VARCHAR(40),
                `policyId` VARCHAR(100),
                FOREIGN KEY(`tagId`) REFERENCES `TAGS`(`tagId`),
                FOREIGN KEY(`policyId`) REFERENCES `POLICIES`(`policyId`),
                PRIMARY KEY(`tagId`, `policyId`))
                '''
            cursor.execute(query)
        except Exception as e:
            print(e)
    
    def add_user(self, user_id: str, user_email: str, user_password: str, user_type: str):
        try:
            user_password = hash_password(user_password)
            cursor = self.mysql.connection.cursor()
            
            #see better way to do this
            if user_type == USER_1:
                query = f'''INSERT INTO POLICYMAKER (pmId, pmEmail, password) VALUES(%s, %s, %s)'''
            elif user_type == USER_2:
                query = f'''INSERT INTO TENDER_AUTHORITY (taId, taEmail, password) VALUES(%s, %s, %s)'''
            elif user_type == USER_3:
                query = f'''INSERT INTO VENDOR (vId, vEmail, password) VALUES(%s, %s, %s)'''
            cursor.execute(query, (user_id, user_email, user_password)) 
            self.mysql.connection.commit()
            cursor.close()
            return 1
        
        except Exception as e:
            print(e)
            return 0

    def login(self, user_email, user_password, user_type):
        try:
            cursor = self.mysql.connection.cursor()
            query_policy = '''SELECT password FROM POLICYMAKER WHERE pmEmail = %s'''
            query_tender = '''SELECT password FROM TENDER_AUTHORITY WHERE taEmail = %s'''
            if user_type == USER_1:
                cursor.execute(query_policy, (user_email,))
            elif user_type == USER_2:
                cursor.execute(query_tender, (user_email,))
            
            account_password = cursor.fetchone()[0]
            cursor.close()
            
            if check_password(user_password, account_password):
                return 1
            return 0
        
        except Exception as e:
            print(e)
            return 0

    def add_tag(self, tags):
        try:
            cursor = self.mysql.connection.cursor()
            tag_id_list = list()
            for tag in tags:
                cursor.execute("SELECT COUNT(tagId) FROM TAGS WHERE tag = %s", (tag,))
                search = cursor.fetchone()[0]
                # print("[DEBUG] SEARCH", search)
                if not search:
                    tag_id = str(uuid.uuid4())[:10]
                    cursor.execute("INSERT INTO TAGS VALUES (%s, %s)", (tag_id, tag,))
                    self.mysql.connection.commit()
                cursor.execute("SELECT tagId FROM TAGS WHERE tag = %s", (tag,))
                tag_id_list.append(cursor.fetchone()[0])
            return tag_id_list
        except Exception as e:
            print(e)
            return 0

    def policy_tag_map(self, policy_id, tag_id_list):
        try:
            cursor = self.mysql.connection.cursor()
            query = "INSERT INTO POLICY_TAGS(tagId, policyId) VALUES(%s, %s)"
            for tag_id in tag_id_list:
                cursor.execute(query, (tag_id, policy_id,))
                self.mysql.connection.commit()
            cursor.close()
        except Exception as e:
            print(e)
            return 0

    def find_dept(self, dept: str):
        try:
            cursor = self.mysql.connection.cursor()
            query = "SELECT deptId FROM DEPARTMENT WHERE deptname = %s"
            cursor.execute(query, (dept))
            dept = cursor.fetchone()
            if not dept:
                return ""
            return dept[0]
        except Exception as e:
            print(e)
            return 0 

    def find_min(self, ministry: str):
        try:
            cursor = self.mysql.connection.cursor()
            query = "SELECT minId FROM MINISTRY WHERE minName = %s"
            cursor.execute(query, (ministry, ))
            dept = cursor.fetchone()
            print("fetched results", dept)
            if not dept:
                return ""
            return dept[0]
        except Exception as e:
            print(e)
            return 0

    def add_policy(self, pm_id, policy, policyname):
        try:
            policy_fol = r""
            policy_fol = os.path.join(policy_fol, str(pm_id))
            policy_path = os.path.join(policy_fol, policyname) #store this path in db
            if not os.path.exists(policy_fol):
                os.makedirs(policy_fol)
            policy.save(policy_path)
            
            cursor = self.mysql.connection.cursor()
            policy_id = uuid.uuid4()
            date, doc_type, ministry, tags = tender_rule_similarity_ml.extract_policy_info(policy_path)
            date = extract_date(date)
            min_id = self.find_min(ministry.lower())
            
            if date is None:
                date = datetime.date.today()
            if min_id:
                query = '''INSERT INTO POLICIES(date, policy, pmId, minId, docType) VALUES(%s, %s, %s, %s, %s)'''
                cursor.execute(query, (date, policy_path, pm_id, min_id, doc_type))
                self.mysql.connection.commit()
            else:
                query = '''INSERT INTO POLICIES(date, policy, pmId, docType) VALUES(%s, %s, %s, %s)'''
                cursor.execute(query, (date, policy_path, pm_id, doc_type))
                self.mysql.connection.commit()
            
            #now insert keywords in the table
            tag_id_list = self.add_tag(tags)
            #if tag not in tags table then insert tag
            self.policy_tag_map(policy_id, tag_id_list)
            cursor.close()
            return 1
            
        except Exception as e:
            print(e)
            return 0

    def extract_tags(self):
        try:
            cursor = self.mysql.connection.cursor()
            query = '''SELECT * FROM TAGS'''
            cursor.execute(query)
            tags_list = cursor.fetchall()
            tags_dict = {}
            for tag in tags_list:
                tags_dict[tag[0]] = tag[1]
            return tags_dict
        except Exception as e:
            print(e)
            return 0
    
    def search_policies(self, policy_id: str, date: str, date_from: str, date_to: str, dept: str, ministry: str, keywords):
        try:
            cursor = self.mysql.connection.cursor()
            #TODO: Fix cursor fetch. This is unsafe and gives 0 if data not present in table 
            dept_id = cursor.execute(f"SELECT deptId FROM DEPARTMENT WHERE deptName = '{dept}'", )
            min_id = cursor.execute(f"SELECT minId FROM MINISTRY WHERE minName = '{ministry}'", )
            tags_dict = self.extract_tags()
            matching_tag_ids = tender_rule_similarity_ml.keyword_similarity(keywords, tags_dict)
            
            matching_policy_ids = []
            for tag_id in matching_tag_ids:
                cursor.execute("SELECT policyId FROM POLICY_TAGS WHERE tagId = %s", (tag_id, ))
                pids = cursor.fetchall()
                for pid in pids:
                    if pid:
                        matching_policy_ids.append(pid[0])

            query = '''SELECT policyId FROM POLICIES 
                     WHERE policyId = %s OR %s is NULL
                        AND minId = %s OR %s IS NULL
                        AND date = %s OR %s IS NULL
                        AND date BETWEEN %s AND %s
                        '''
            cursor.execute(query, (policy_id, policy_id, min_id, min_id, date, date, date_from, date_to))
            policy_list = cursor.fetchall()

            policy_id_list = []
            for pol_id in policy_list:
                policy_id_list.append(pol_id[0])
            for pol_id in matching_policy_ids:
                policy_id_list.append(pol_id)
            
            policy_names = []
            for policy_id in policy_id_list:
                cursor.execute("SELECT policy from POLICIES WHERE policyId = %s", (policy_id,))
                name = cursor.fetchone()[0]
                if name not in policy_names:
                    policy_names.append(name)

            return policy_names#sending back list of policy names

        except Exception as e:
            print(e)
            return 0
      
#how is connection handled in mysqldb 
class TenderDB:
    def __init__(self, mysql:MySQL) -> None:
        #tender related db interactions 
        self.mysql = mysql
        cursor = self.mysql.connection.cursor()

        #create tender-authority db
        try:
            query = '''CREATE TABLE if not exists `TENDER_AUTHORITY` (
                `taId` VARCHAR(100) PRIMARY KEY, 
                `taName` VARCHAR(50), 
                `taEmail` VARCHAR(100),
                `password` VARCHAR(100),
                `sector` ENUM('government', 'private'))'''
            cursor.execute(query)
        except Exception as e:
            print(e)

        #create tender db
        try:
            query = '''CREATE TABLE if not exists `TENDERS` ( 
             `tenderId` VARCHAR(100) PRIMARY KEY,
             `date` DATE NOT NULL , 
             `tender` MEDIUMBLOB NOT NULL,
             `taId` VARCHAR(100),
             FOREIGN KEY(`taId`) REFERENCES `TENDER_AUTHORITY`(`taId`))'''
            cursor.execute(query)
        except Exception as e: 
            print(e)

        #create vender db
        try:
            query = '''CREATE TABLE IF NOT EXISTS `VENDOR` (
                `vId` VARCHAR(100) PRIMARY KEY, 
                `vName` VARCHAR(50), 
                `vEmail` VARCHAR(100),
                `password` VARCHAR(100))'''
            cursor.execute(query)
        except Exception as e:
            print(e)
            return 0
        
        #create tender-vendor mapping
        try:
            query = '''CREATE TABLE IF NOT EXISTS `TENDER_VENDOR` (
                `tenderId` VARCHAR(100), 
                `vId` VARCHAR(100),
                `document` VARCHAR(500),
                FOREIGN KEY(`tenderId`) REFERENCES `TENDERS`(`tenderId`),
                FOREIGN KEY(`vId`) REFERENCES `VENDOR`(`vId`),
                PRIMARY KEY (tenderId, vId, document))'''
            cursor.execute(query)
        except Exception as e:
            print(e)
            return 0
        
        try:
            query = '''CREATE TABLE IF NOT EXISTS `TENDER_REQUIREMENTS` (
                `tenderId` VARCHAR(100),
                `documents` VARCHAR(5000),
                `eligibility` VARCHAR(5000),
                FOREIGN KEY(`tenderId`) REFERENCES `TENDERS`(`tenderId`),
                PRIMARY KEY (tenderId))'''
            cursor.execute(query)
        except Exception as e:
            print(e)
            return 0
        
        
    #check compliance
    def add_tender(self, tender_id: str, ta_id: str, tender_name: str, tender):
        try:
            tender_fol = r""
            tender_path = os.path.join(tender_fol, tender_name) #store this path in db
            if not os.path.exists(tender_fol):
                os.makedirs(tender_fol)
            tender.save(tender_path)
            
            policy_compliance_scores = tender_rule_similarity_ml.find_similarity(tender_path)
            subset_policies = {k: v for k, v in policy_compliance_scores.items() if k.startswith("Policy") and int(k[6:]) <= 10}
            # Sort the subset in descending order by score
            sorted_policies = sorted(subset_policies.items(), key=lambda item: item[1], reverse=True)
            return sorted_policies
        
        except Exception as e:
            print(e)
            return 0

    def publish_tender(self, tender_id: str, ta_id: str, tender_name: str, date: str, tender):
        try:
            tender_fol = r""
            tender_path = os.path.join(tender_fol, tender_name) #store this path in db
            if not os.path.exists(tender_fol):
                os.makedirs(tender_fol)
            tender.save(tender_path)
            
            cursor = self.mysql.connection.cursor()
            
            #TODO: Find docs to upload for tender & who is eligible to participate in tender
            tender_requirements = tender_rule_similarity_ml.find_tender_requirements(tender_path)
            docs, eligibility = tender_requirements['pdf'], tender_requirements['eligibility']
            #insert tender requirements into the respective table
            
            print("[DEBUG] TENDER REQUIREMENTS", tender_requirements)
            query = '''INSERT INTO TENDERS(tenderId, date, tender, taId) VALUES(%s, %s, %s, %s)'''
            cursor.execute(query, (tender_id, date, tender_path, ta_id,))
            self.mysql.connection.commit()
            
            query = '''INSERT INTO TENDER_REQUIREMENTS(tenderId, documents, eligibility) VALUES (%s, %s, %s)'''
            cursor.execute(query, (tender_id, docs, eligibility))
            self.mysql.connection.commit()
            
            cursor.close()
            return 1

        except Exception as e:
            print(e)
            return 0

    def fetch_tenders(self, ta_id: str):
        try:
            cursor = self.mysql.connection.cursor()
            query = ('''SELECT * FROM TENDERS WHERE
                              taId = %s OR %s IS NULL''')
            cursor.execute(query, (ta_id, ta_id,))
            tenders_list = cursor.fetchall()
            return tenders_list
            
        except Exception as e:
            print("[DEBUG]", e)
            return 0

    def add_vendor(self, vid: str, vemail: str, vpassword):
        try:
            vpassword = hash_password(vpassword)
            cursor = self.mysql.connection.cursor()
            query = '''INSERT INTO VENDER(vId, vEmail, password) VALUES(%s, %s, %s)'''
            cursor.execute(query, (vid, vemail, vpassword))
            self.mysql.connection.commit()
            cursor.close()
            return 1
        
        except Exception as e:
            print(e)
            return 0

    def add_bid(self, vid: str, tender_id: str, documents:list, dnames: list[str]):
        try:
            cursor = self.mysql.connection.cursor()
            docu_fol = r""
            docu_fol = os.path.join(docu_fol, str(tender_id), str(vid)) #each doducment will be stored under that vendor id under that tendor 
            if not os.path.exists(docu_fol):
                os.makedirs(docu_fol)
            for idx, document in enumerate(documents):
                #TODO: extract documents to upload, which services can apply to that tender
                #TODO: (chatbot) if I am eligible to do it
                #TODO: Check compliance with tender
                docu_path = os.path.join(docu_fol, dnames[idx])
                document.save(docu_path)
                query = '''INSERT INTO TENDER_VENDOR(tenderId, vId, document) VALUES (%s, %s, %s)'''
                cursor.execute(query, (tender_id, vid, docu_path))
                self.mysql.connection.commit()
            cursor.close()
            return 1
        except Exception as e:
            print(e)
            return 0

    #fetch all bidders and their uploaded documents for the tender
    def fetch_bid(self, tender_id: str):
        try:
            cursor = self.mysql.connection.cursor()
            query = '''SELECT * FROM TENDER_VENDOR WHERE `tenderId` = %s'''
            cursor.execute(query, (tender_id, ))
            vendors_docs = cursor.fetchall()
            cursor.close()
            return vendors_docs
        except Exception as e:
            print(e)
            return 0

    def bid_chatbot(self, question: str, tender_id: str):
        try:
            cursor = self.mysql.connection.cursor()
            query = '''SELECT eligibility from TENDER_REQUIREMENTS WHERE tenderId = %s'''
            cursor.execute(query, (tender_id,))
            eligibility = cursor.fetchone()
            response = []
            if eligibility:
                eligibility = eligibility[0]
                response = tender_rule_similarity_ml.bid_chatbot(question, eligibility)
            return response["answer"]
        except Exception as e:
            print(e)
            return 0
            
    def bid_documents_check(self, docs):
        try:
            cursor = self.mysql.connection.cursor()
            ai_cmmts = {}
            #store doc name against comments: passed or not
            for doc in docs:
                docname = doc.filename
                 #store the doc locally 
                bidder_doc_fol = r""
                if 'aadhar' in docname:
                    bidder_doc_path = os.path.join(bidder_doc_fol, "aadhar", docname)
                    doc.save(bidder_doc_path)
                    status = bidder_doc_check.process_pdf_and_check_correctness(bidder_doc_path)
                    ai_cmmts[docname] = status
                else:
                    bidder_doc_path = os.path.join(bidder_doc_fol, "pan", docname)
                    doc.save(bidder_doc_path)
                    status = bidder_doc_check.process_pan_card(bidder_doc_path)
                    ai_cmmts[docname] = status
            return ai_cmmts
        
        except Exception as e:
            print(e)
            return 0
        