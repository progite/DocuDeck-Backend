#should the tender and rules database be in separate files?
import os
from flask_mysqldb import MySQL
from flask import current_app
from password_utils import hash_password, check_password
from constants import USER_1, USER_2, USER_3

#Could have maintained combined db for all users with diff user types but then have to implement diff authorization rules. 
#This is more compact

class PolicyDB:
    def __init__(self, mysql: MySQL) -> None:
        # print(current_app.config)
        self.mysql = mysql
        # conn = self.mysql.connect()
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
    
    def add_policymaker(self, pm_id: str, pm_email: str, pm_password: str):
        try:
            pm_password = hash_password(pm_password)
            cursor = self.mysql.connection.cursor()
            query = '''INSERT INTO POLICYMAKER(pmId, pmEmail, password) VALUES(%s, %s, %s)'''
            cursor.execute(query, (pm_id, pm_email, pm_password))
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

    def add_policy(self, pm_id, policy, policyname):
        try:
            policy_fol = r"C:\Users\progg\Desktop\desktop_p\DocuDeck\Scraper\policies\\rulesandprocs"
            policy_fol = os.path.join(policy_fol, str(pm_id))
            policy_path = os.path.join(policy_fol, policyname) #store this path in db
            if not os.path.exists(policy_fol):
                os.makedirs(policy_fol)
            policy.save(policy_path)
            
            cursor = self.mysql.connection.cursor()
            # # TODO: ml integration
            # #department, ministry = ml integrate
            dept_id = min_id = 1
            policy_id = 2
            date = "2023-10-10"
            query = '''INSERT INTO POLICIES(policyId, date, policy, pmId, deptId, minId) VALUES(%s, %s, %s, %s, %s, %s)'''
            cursor.execute(query, (policy_id, date, policy_path, pm_id, dept_id, min_id))
            self.mysql.connection.commit()
            
            cursor.close()
            return 1
        except Exception as e:
            print(e)
            return 0

    def search_policies(self, policy_id: str, date: str, date_from: str, date_to: str, dept: str, ministry: str):
        try:
            cursor = self.mysql.connection.cursor()
            #first get dept and ministry from pmid
            #TODO: Fix cursor fetch. This is unsafe and gives 0 if data not present in table 
            dept_id = cursor.execute(f"SELECT deptId FROM DEPARTMENT WHERE deptName = '{dept}'", )
            min_id = cursor.execute(f"SELECT minId FROM MINISTRY WHERE minName = '{ministry}'", )
            print(dept_id, min_id, date)
            query = '''SELECT policy FROM POLICIES WHERE 
                        (pmId = %s OR %s is NULL)
                        AND (deptId = %s OR %s IS NULL) 
                        AND (minId = %s OR %s IS NULL) 
                        AND (date = %s OR %s IS NULL)
                        AND (date BETWEEN %s AND %s) 
                        '''
            cursor.execute(query, (policy_id, policy_id, dept_id, dept_id, min_id, min_id, date, date, date_from, date_to))
            policy_list = cursor.fetchall() 
            print("[DEBUG] POLICY_LIST", policy_list)
            return policy_list #sending back list of policy names
           
        except Exception as e:
            print(e)
            return 0
    
            
#how is connection handled in mysqldb 
class TenderDB:
    def __init__(self, mysql:MySQL) -> None:
        #tender related db interactions 
        self.mysql = mysql
        cursor = self.mysql.connection.cursor()

        #create user db
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

    def add_tender(self, tender_id: str, ta_id: str, tender_name: str, date: str, tender):
        try:
            tender_fol = r"C:\Users\progg\Desktop\desktop_p\DocuDeck\Tenders"
            tender_path = os.path.join(tender_fol, tender_name) #store this path in db
            if not os.path.exists(tender_fol):
                os.makedirs(tender_fol)
            tender.save(tender_path)
            
            #TODO: check compliance and if compliant
            cursor = self.mysql.connection.cursor()
            query = '''INSERT INTO TENDERS(tenderId, date, tender, taId) VALUES(%s, %s, %s, %s)'''
            cursor.execute(query, (tender_id, date, tender_path, ta_id,))
            self.mysql.connection.commit()
            
            cursor.close()
            return 1

            #if not compliant
            return 0    

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

# class BidderDB:
    # def __init__(self, mysql) -> None:
    #     #Info about Bidders
    #     self.mysql = mysql
    #     conn = self.mysql.connect()
    #     cursor = conn.cursor()

    #     #create user db
    #     #create bidder db
    #     cursor.close()
    #     conn.close()


