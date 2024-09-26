from flask import Flask, render_template, make_response, request as rq
from dotenv import load_dotenv as LoadEnvVariables
from os import environ
from utils import MakeRequest
from base64 import b64encode
from db import NPCS

LoadEnvVariables()
app = Flask(__name__)
db = NPCS()
app.config['SECRET_KEY'] =  environ.get("FLASK_KEY")
client_auth = f"{environ.get('OAUTH_CLIENT_ID')}:{environ.get('OAUTH_CLIENT_SECRET')}"
client_auth = b64encode(client_auth.encode()).decode()

def addNotionAuth(res):
    
    db.get_table("Person")._Create({
        "homepage": res["duplicated_template_id"],
        "person_id": res["owner"]["user"]["id"]
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

@app.route('/', methods = ["GET"])
def index():
    variables = {"url": environ.get("NOTION_AUTH_URL")}
    return make_response(render_template("index.html", **variables))

@app.route('/notioned', methods = ["GET"])
def notioned():
    variables = {"url": environ.get("NOTION_AUTH_URL")}
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
    return make_response(render_template("index.html", **variables))


if __name__ == "__main__":
    app.run(
        debug=True
    )