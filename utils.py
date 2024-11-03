from requests import request, exceptions
from json import loads
from datetime import datetime
import mysql.connector as sql
from datetime import datetime
from typing import Union


def MakeRequest(method: str, url: str, message: str, data: dict = None, headers={}, raw: bool = False, returnError: bool = False):
    if data is None:
        res = request(method=method, url=url, headers=headers)
    else:
        res = request(method=method, url=url, json=data, headers=headers)
    print(f"{res.status_code} | {method} | {url.replace("https://", "").split("/", 1)[0]} | {message}")
    try:
        res.raise_for_status()
        if res.status_code == 200:
            return (res if raw else loads(res.text))
    except exceptions.HTTPError as e:
        if returnError:
            return e
        print(f"URL: {e.response.url}")
        print(f"Response Message: {e.response.text}")
        exit(1)

def QueryNotion(url, message, blockQuery=False, query={}):
    # Integrates Pagenation to collet all objects from notion
    results = []
    more = True
    method = "GET" if blockQuery else "POST"
    while more:
        Data = MakeRequest(method, url, message, query)
        results += Data["results"]
        more = Data.get("has_more", False)
        if more:
            query["start_cursor"] = Data["next_cursor"]
    return results

def ListPossibleStartYears(start_year="201617"):
    # Extract the current year
    current_year = datetime.now().year
    
    # Initialize the start year and list to hold academic years
    start_year_int = int(start_year[:4])  # Extract the start year as an integer
    academic_years = []
    
    # Generate academic years until the current year
    while start_year_int < current_year+2:
        # Construct the next academic year string
        next_year = start_year_int + 1
        academic_year = f"{start_year_int}{str(next_year)[-2:]}"
        academic_years.append(academic_year)
        
        # Increment the year
        start_year_int += 1
    
    academic_years.reverse()
    return academic_years

def GetAcademicYear():
    now = datetime.now()
    
    # Determine the academic year
    if now.month >= 7:  # If the month is July (7) or later
        start_year = now.year
        end_year = now.year + 1
    else:  # If the month is earlier than September
        start_year = now.year - 1
        end_year = now.year

    return f"20{start_year % 100:02d}{end_year % 100:02d}"


def NotionURLToID(url: str) -> str:
    # Turns the URL of a Notion page into its ID
    parts = url.split("/")
    if len(parts) >= 2:
        return parts[-1].split("-")[-1].split("?")[0]
    else:
        print("No URL entered.")
        exit()

class _Database():
    def __init__(self, user, pwd, name):  # Connect and create database
        self.__config = {}
        self.__config.update({
                        "host": "localhost",
                         "user": user,
                         "password": pwd
        })
        conn = sql.connect(**self.__config)
        c = conn.cursor(dictionary=True)
        c.execute(f"CREATE DATABASE IF NOT EXISTS {name};")
        conn.close()
        self.__config.update({"database": name})
        self.conn = None
        self.cursor = None


    def _GetName(self):
        return self.__config["database"]
    
    def _StartTransaction(self):
        if (self.conn and self.conn.is_connected() and self.cursor):
            return
        self.conn = sql.connect(**self.__config)
        self.cursor = self.conn.cursor(dictionary=True)
        self.cursor.execute(f"""START TRANSACTION;""")
    
    def _EndTransaction(self):
        if not (self.conn and self.conn.is_connected() and self.cursor):
            return
        print("-" * 20)
        self.cursor.execute(f"""COMMIT;""")
        self.conn.close()

    # General Subroutines

    def _SQLCommand(self, command):  # Connect and perform an SQL Command
        self._StartTransaction()
        print(f"SQL REQUEST | {command}\nRESPONSE |", end=" ")
        self.cursor.execute(f"""{command};""")
        rows = (self.cursor.fetchall())
        data = [dict(row) for row in rows]
        print(str(data))
        return data

    def _ProtectFromInjection(self, rawValue):
        value = ""
        for i in rawValue:
            if i in ("'", '"', "\\"):
                value = value + "\\"
            value = value + i
        return value

    def get_table(self, name=None) -> Union["Entity", dict[str, "Entity"]]:
        if name is None:
            return self._Tables
        return self._Tables.get(name, self._Tables)


class Entity():
    def __init__(self, database, createCommand):
        self._Database = database
        self._TableName = self.__class__.__name__
        self._Database._SQLCommand(
            f"""CREATE TABLE IF NOT EXISTS `{self._TableName}` ({createCommand})""")

    # Getters and Setters

    def _GetTableName(self):
        return self._TableName

    # CRUD

    def _Create(self, data={}):
        query = f"INSERT IGNORE INTO `{self._TableName}`"
        attributes = []
        values = []
        for attribute, value in data.items():
            if value != None:
                attributes.append(f"`{attribute}`")
                if type(value) in (int, float, bool):
                    values.append(str(value))
                elif type(value) == datetime:
                    values.append(f"'{str(value)}'")                
                else:
                    value = self._Database._ProtectFromInjection(value)
                    values.append(f"'{str(value)}'")
        query += "(" + ", ".join(attributes) + ") VALUES (" + ", ".join(values) + ")"
        self._Database._SQLCommand(query)

    def _Retrieve(self, conditions={}):
        query = f"SELECT * FROM `{self._TableName}`"
        filters = self.__SplitParameters(conditions)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        results = self._Database._SQLCommand(query)
        return results

    def _Update(self, atributes={}, conditions={}):
        query = f"UPDATE `{self._TableName}`"
        data = self.__SplitParameters(atributes, False)
        if data:
            query += " SET " + ", ".join(data)
        filters = self.__SplitParameters(conditions)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        self._Database._SQLCommand(query)

    def _Delete(self, conditions={}):
        query = f"DELETE FROM `{self._TableName}`"
        filters = self.__SplitParameters(conditions)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        self._Database._SQLCommand(query)

    # General Subroutines

    # Turns a a list of parameters into an SQL statement
    def __SplitParameters(self, data, searchingStatement=True):
        parameters = []
        for attribute, value in data.items():
            if value != None:
                if type(value) in (int, float):
                    parameters.append(f"`{attribute}` = {str(value)}")
                elif type(value) == datetime:
                    parameters.append(f"`{attribute}` = '{str(value)}'")
                else:
                    value = self._Database._ProtectFromInjection(value)
                    parameters.append(f"`{attribute}` = '{str(value)}'")
            # If the query is being used to find an item (and is None)
            elif searchingStatement:
                parameters.append(f"`{attribute}` IS NULL")
            elif not searchingStatement:
                parameters.append(f"`{attribute}` = NULL")
        return parameters