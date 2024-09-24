from flask import Flask, render_template, make_response
import os
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] =  os.environ.get("FLASK_KEY")

@app.route('/')
def hello_world():
    variables = {"url": os.environ.get("NOTION_AUTH_URL")}
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
            "Authorization": f"Basic {os.environ.get('OAUTH_CLIENT_ID')}:{os.environ.get('OAUTH_CLIENT_SECRET')}",
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