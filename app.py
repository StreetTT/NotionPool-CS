import os
import requests
from flask import Flask, render_template, make_response, request as rq
from utils import MakeRequest
from base64 import b64encode

app = Flask(__name__)
app.config['SECRET_KEY'] =  os.environ.get("FLASK_KEY")
client_auth = f"{os.environ.get('OAUTH_CLIENT_ID')}:{os.environ.get('OAUTH_CLIENT_SECRET')}"
client_auth = b64encode(client_auth.encode()).decode()

@app.route('/', methods = ["GET", "POST"])
def index():
    variables = {"url": os.environ.get("NOTION_AUTH_URL")}
    variables.update({"error": True})
    variables.update({"data": {}})
    return make_response(render_template("index.html", **variables))

@app.route('/notioned', methods = ["GET", "POST"])
def notioned():
    variables = {}
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
    print(res)
    variables.update({"url": os.environ.get("NOTION_AUTH_URL")})
    variables.update({"data": res})

    return make_response(render_template("index.html", **variables))


if __name__ == "__main__":
    app.run(
        debug=True
    )