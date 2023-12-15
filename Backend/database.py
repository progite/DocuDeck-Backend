#should the tender and rules database be in separate files?
from flask_mysqldb import MySQL
from flask import current_app

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
                `policy` MEDIUMBLOB NOT NULL,
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
    def add_policy(self, policy_id: str, date: str, policy, pm_id):
        try:
            cursor = self.mysql.connection.cursor()
            # report = base64.b64decode(report)
            # report = compress_data(report)
            # TODO: ml integration
            #department, ministry = ml integrate
            dept_id = min_id = 1
            query = '''INSERT INTO POLICIES(policyId, date, policy, pmId, deptId, minId) VALUES(%s, %s, %s, %s, %s, %s)'''
            cursor.execute(query, (policy_id, date, policy, pm_id, dept_id, min_id))
            self.mysql.connection.commit()
            # print("[DEBUG], ENTERED HERE")
            
            cursor.close()
            return 1
        except Exception as e:
            print("[DEBUG]", e)
            return 0

    def search_policies(self, policy_id: str, date: str, date_from: str, date_to: str, dept: str, ministry: str):
        try:
            cursor = self.mysql.connection.cursor()
            #first get dept and ministry from pmid
            #TODO: Fix cursor fetch. This is unsafe and gives 0 if data not present in table 
            dept_id = cursor.execute(f"SELECT deptId FROM DEPARTMENT WHERE deptName = '{dept}'", )
            min_id = cursor.execute(f"SELECT minId FROM MINISTRY WHERE minName = '{ministry}'", )
            print(dept_id, min_id, date)
            query = '''SELECT policyid FROM POLICIES WHERE 
                        (pmId = %s OR %s is NULL)
                        AND (deptId = %s OR %s IS NULL) 
                        AND (minId = %s OR %s IS NULL) 
                        AND (date = %s OR %s IS NULL)
                        AND (date BETWEEN %s AND %s) 
                        '''
            cursor.execute(query, (policy_id, policy_id, dept_id, dept_id, min_id, min_id, date, date, date_from, date_to))
            policy_list = cursor.fetchall()
            return policy_list 
           
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
                `password` VARCHAR(100),
                `sector` ENUM('government', 'private'))'''
            cursor.execute(query)
        except Exception as e:
            print(e)

        #create tender db
        try:
            query = '''CREATE TABLE if not exists `TENDERS` ( 
             `tenderId` VARCHAR(100) NOT NULL,
             `date` DATE NOT NULL , 
             `tender` MEDIUMBLOB NOT NULL,
             `taId` VARCHAR(100),
             FOREIGN KEY(`taId`) REFERENCES `TENDER_AUTHORITY`(`taId`))'''
            cursor.execute(query)
        except Exception as e: 
            print(e)

    def fetch_tenders(self):
        try:
            cursor = self.mysql.connection.cursor()
            cursor.execute("SELECT * FROM TENDERS")
            tenders_list = cursor.fetchall()
            return tenders_list
            
        except Exception as e:
            print("[DEBUG]", e)
            return 0
    

    def store_tender(self, ):
        pass

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


