from requests import request, exceptions
from json import loads
from datetime import datetime
import mysql.connector as sql
from datetime import datetime


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


    def _GetName(self):
        return self.__config["database"]

    # General Subroutines

    def _SQLCommand(self, command):  # Connect and perform an SQL Command
        print(f"SQL REQUEST | {command}\nRESPONSE |", end=" ")
        conn = sql.connect(**self.__config)
        c = conn.cursor(dictionary=True)
        c.execute(f"""START TRANSACTION;""")
        c.execute(f"""{command};""")
        rows = (c.fetchall())
        data = [dict(row) for row in rows]
        print(str(data))
        c.execute(f"""COMMIT;""")
        conn.close()
        return data

    def _ProtectFromInjection(self, rawValue):
        value = ""
        for i in rawValue:
            if i in ("'", '"', "\\"):
                value = value + "\\"
            value = value + i
        return value

    def get_table(self, name=None) -> "Entity" | dict[str,"Entity"]:
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
                if type(value) in (int, float):
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