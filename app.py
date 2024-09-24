from flask import Flask, render_template, make_response
from dotenv import load_dotenv as LoadEnvVariables
from os import getenv
import requests

LoadEnvVariables()
app = Flask(__name__)
app.config['SECRET_KEY'] =  getenv("FLASK_KEY")

@app.route('/')
def hello_world():
    variables = {"url": getenv("NOTION_AUTH_URL")}
    return make_response(render_template("index.html", **variables))

@app.route('/notioned')
def notioned():
    code = requests.args.get('code', default = "", type = str)

    res = requests.post(
        "https://api.notion.com/v1/oauth/token",
        {
            "grant_type":"authorization_code",
            "code":code,
            "redirect_uri":"https%3A%2F%2Fnotionpoolcs.onrender.com%2Fnotioned"
        },
        headers={
            "Authorization": f"Basic {getenv('OAUTH_CLIENT_ID')}:{getenv('OAUTH_CLIENT_SECRET')}",
            "Content-Type": "application/json"
        }
    )
    with open("response.txt", "w") as f:
        f.write(res)
    return make_response(render_template("index.html"))

if __name__ == "__main__":
    app.run(
        debug=True
    )