from requests import request, exceptions
from json import loads
from datetime import datetime as dt


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
        # exit(1)

def Query(url, message, blockQuery=False, query={}):
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

def get_academic_year(date:dt):
    # Extract the year and month from the date
    year = date.year
    
    # Determine the academic year
    if date.month >= 6:  # If the month is June (6) or later
        start_year = year
        end_year = year + 1
    else:  # If the month is earlier than September
        start_year = year - 1
        end_year = year
    
    # Format the academic year as YYYYYY
    return f"20{start_year % 100:02d}{end_year % 100:02d}"