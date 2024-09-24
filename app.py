import os
import requests
from flask import Flask, render_template, make_response, request as rq
from requests import request, exceptions
from json import loads


def MakeRequest(method: str, url: str, message: str, data: dict = None, headers={}, raw: bool = False, returnError: bool = False):
    if data is None:
        res = request(method=method, url=url, headers=headers)
    else:
        res = request(method=method, url=url, json=data, headers=headers)
    print(f"{res.status_code} | {method} | {url.removeprefix("https://").split("/", 1)[0]} | {message}")
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

LoadEnvVariables()
app = Flask(__name__)
app.config['SECRET_KEY'] =  os.environ.get("FLASK_KEY")

@app.route('/', methods = ["GET", "POST"])
def hello_world():
    variables = {"url": os.environ.get("NOTION_AUTH_URL")}
    return make_response(render_template("index.html", **variables))

@app.route('/notioned', methods = ["GET", "POST"])
def notioned():
    variables = {}
    code = rq.args.get('code', default = "", type = str)
    res = MakeRequest(
        "POST",
        "https://api.notion.com/v1/oauth/token",
        data={
            "grant_type":"authorization_code",
            "code":code,
            "redirect_uri":"https%3A%2F%2Fnotionpoolcs.onrender.com%2Fnotioned"
        },
        headers={
            "Authorization": f"Basic {os.environ.get('OAUTH_CLIENT_ID')}:{os.environ.get('OAUTH_CLIENT_SECRET')}",
            "Content-Type": "application/json"
        }
    )
    print(res)
    variables.update({"url": os.environ.get("NOTION_AUTH_URL")})
    variables.update({"error": res.get("error", False)})
    if not res.get("error", False):
        variables.update({"data": res})

    return make_response(render_template("index.html", **variables))


if __name__ == "__main__":
    app.run(
        debug=True
    )