from flask import Flask, render_template, make_response, request as rq, redirect, flash
from dotenv import load_dotenv as LoadEnvVariables
from os import environ
from utils import MakeRequest, ListPossibleStartYears
from base64 import b64encode
from db import NPCS
import re
from main import *

LoadEnvVariables()
app = Flask(__name__)
db = NPCS()
app.config['SECRET_KEY'] =  environ.get("FLASK_KEY")
client_auth = f"{environ.get('OAUTH_CLIENT_ID')}:{environ.get('OAUTH_CLIENT_SECRET')}"
client_auth = b64encode(client_auth.encode()).decode()

def addNotionAuth(res):
    db.get_table("Person")._Create({
        "homepage": res["duplicated_template_id"],
        "person_id": res["owner"]["user"]["id"],
        "start_year": GetAcademicYear()
    })
    db.get_table("NotionApp")._Create({
        "access_token": res["access_token"],
        "token_type": res["token_type"],
        "bot_id": res["bot_id"],
        "person_id": res["owner"]["user"]["id"]
    })
    db.get_table("NotionWorkspace")._Create({
        "name": res["workspace_name"],
        "icon": res["workspace_icon"],
        "workspace_id": res["workspace_id"],
        "bot_id": res["bot_id"]
    })
    db._EndTransaction()


@app.route('/', methods = ["GET"])
def index():
    variables = {"loggedIn": False}
    # Check if a person is logged in
    notionID = rq.cookies.get('notionID', "")
    if not notionID:
        output = make_response(render_template("index.html", **variables))
        return output
    variables["loggedIn"] = True
    person = db.get_table("Person")._Retrieve({"person_id": notionID})[0]
    variables["startYears"] = ListPossibleStartYears()
    variables["currentStartYear"] = person["start_year"]
    # Get all modules
    modules = db.get_table("Modules")._Retrieve({"person_id": notionID})
    variables["modules"] = {}
    for module in modules:
       key = AcaYearToText(module["year"], person["start_year"])
       variables["modules"].setdefault(key, []).append({
           "moduleID": module['module_id'], 
           "pushed": module['pushed'], 
           "moduleNotionID": (module["module_notion_id"] if module["module_notion_id"] else person['modules']).replace("-","")

       })
    variables["homepage"] = person['homepage'].replace("-","")
    print(variables)
    output = make_response(render_template("index.html", **variables))
    db._EndTransaction()
    return output

@app.route('/newcourse', methods = ["POST"])
def newcourse():
    notionID = rq.cookies.get('notionID', "")
    if not notionID:
        return redirect("/")
    form = rq.form.to_dict()
    pushed = 1 if form.get("push", False) else 0
    db.get_table("Modules")._Create({
        "module_id": form["code"],
        "year": GetAcademicYear(),
        "pushed": pushed,
        "person_id":notionID
        
    })
    if pushed:
        ParseModules([form["code"]], db, notionID)
    db._EndTransaction()
    return redirect("/")

@app.route('/notioned', methods = ["GET"])
def notioned():
    code = rq.args.get('code', default = "", type = str)
    res = MakeRequest(
        "POST",
        "https://api.notion.com/v1/oauth/token",
        "OAuth2 request",
        data={
            "grant_type":"authorization_code",
            "code":code,
            "redirect_uri":"https://notionpoolcs.onrender.com/notioned"
        },
        headers={
            "Authorization": f"Basic {client_auth}",
            "Content-Type": "application/json"
        }
    )
    addNotionAuth(res)
    output = make_response(redirect("/"))
    output.set_cookie("notionID", res["owner"]["user"]["id"])
    return output


if __name__ == "__main__":
    # from test import sampleRes
    # addNotionAuth(sampleRes)
    app.run(
        debug=True
    )