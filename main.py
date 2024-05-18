from os import getenv
from requests import request, exceptions
from sys import exit
from json import loads
from datetime import datetime as dt
from datetime import timedelta as td
from dotenv import load_dotenv as LoadEnvVariables
from random import choices
from bs4 import BeautifulSoup

# Get Globals
LoadEnvVariables()
NOTIONTOKEN = getenv("notiontoken")
HEADERS = {
    "Authorization": f"Bearer {NOTIONTOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

YEARS = {
    "202324": "First [23-24]",
    "202425": "Second [24-25]",
    "202526": "Third [25-26]",
    "202627": "Fourth [26-27]"
}

SEMESTERS = {
    "Second Semester" : "Second [Jan-May]",
    "First Semester" : "First [Sep-Dec]"
}


# General Subroutines


def MakeRequest(method: str, url: str, message: str, data: dict = None):
    if data is None:
        res = request(method=method, url=url, headers=HEADERS)
    else:
        res = request(method=method, url=url, json=data, headers=HEADERS)
    print(f"{res.status_code} | {method} | {message}")
    try:
        res.raise_for_status()
        if res.status_code == 200:
            return loads(res.text)
        else:
            print("Error: Unexpected status code.")
    except exceptions.HTTPError as e:
        print(f"URL: {e.response.url}")
        print(f"Response Message: {e.response.text}")
        exit(1)


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
    if date.month >= 5:  # If the month is May (5) or later
        start_year = year
        end_year = year + 1
    else:  # If the month is earlier than September
        start_year = year - 1
        end_year = year
    
    # Format the academic year as YYYYYY
    return f"20{start_year % 100:02d}{end_year % 100:02d}"



if __name__ == "__main__":
    modules = {"COMP201": None}
    MODULEDBID = NotionURLToID(getenv("moduleurl"))
    ASSIGNMENTDBID = NotionURLToID(getenv("assignmenturl"))
    ASSESSMENTDBID = NotionURLToID(getenv("assesmenturl"))
    for moduleCode in modules:
        # Setting Up the Module Page

        acaYear = get_academic_year(dt.now())
        url = f"https://tulip.liv.ac.uk/mods/student/cm_{moduleCode}_{acaYear}.htm"
        res = request("GET", url)
        soup = BeautifulSoup(res.content, 'html.parser')
        tables = soup.find_all('table', align='center')
        
        for table in tables:
            rows = table.find_all('tr', valign='Top')
            
            for row in rows:
                headers = row.find_all('td', class_='ddheader')
                cells = row.find_all('td', class_='dddefault')

                if headers and cells and headers[0].get_text(strip=True) in ["1.", "6.", "8.","9.","14.", "15.", "16."] :
                    headerNo = headers[0].get_text(strip=True)
                    
                    if headerNo == "1.": # Name
                        title = cells[0].get_text(strip=True)
                    
                    elif headerNo == "6.": # Semester
                        semester = cells[0].get_text(strip=True)
                    
                    elif headerNo == "8.": # Credits
                        creds = cells[0].get_text(strip=True)

                    elif headerNo == "9.": # Teacher
                        teacher = cells[0].get_text().strip().split("\n")
                        teacherEmail = teacher[2].strip()
                        teacher = teacher[0].strip()

                    elif headerNo == "14.": # Study Times
                        studyTimes = {
                            "Study Hours": {},
                            "Private Study": None,
                            "Total Hours": None
                        }
                        studyTimes["Study Hours"]["Lectures"] = cells[0].get_text(strip=True)
                        studyTimes["Study Hours"]["Seminars"] = cells[1].get_text(strip=True)
                        studyTimes["Study Hours"]["Tutorials"] = cells[2].get_text(strip=True)
                        studyTimes["Study Hours"]["Lab Practicals"] = cells[3].get_text(strip=True)
                        studyTimes["Study Hours"]["Fieldwork Placement"] = cells[4].get_text(strip=True)
                        studyTimes["Study Hours"]["Other"] = cells[5].get_text(strip=True)
                        studyTimes["Study Hours"]["Total"] = cells[6].get_text(strip=True)

                    elif headerNo == "15.":
                        studyTimes["Private Study"] = cells[1].get_text(strip=True)

                    elif headerNo == "16.":
                        studyTimes["Total Hours"] = cells[1].get_text(strip=True)

        # Assessment     
        table = soup.find('td', string='Assessment').find_parent('table')
        assessments = []
        rows = table.find_all('tr')[5:-1]  # Exclude header row
        for row in rows:
            cells = row.find_all('td')
            assessments.append({
                "Assessment": cells[0].text.strip(),
                "Type": cells[1].text.strip(),
                "Weighting": int(cells[2].text.strip()),
                "Learning Outcomes": cells[5].text.strip().split(', ')
            })
        
        # Aims
        table = soup.find('td', string='Aims').find_parent('table')
        aims = table.find_all('tr')[2].contents[3].get_text(strip=True)

        # Learning Objectives
        table = soup.find('td', string='Learning Outcomes').find_parent('table')
        los = {}
        rows = table.find_all('tr')[2:]  # Exclude header row
        for row in rows:
            cells = row.find_all('td')
            txt = cells[1].text.strip()
            outerBracket = txt.find(")")
            los[txt[1:outerBracket]] = txt[outerBracket+1:].strip()

        # Syllabus
        table = soup.find('td', string='Syllabus').find_parent('table')
        syllabus = table.find_all('td')[2].contents[1].get_text(strip=True)
        
        modules[moduleCode] = MakeRequest(
            # Create a new Module Page
            "POST",
            f"https://api.notion.com/v1/pages",
            "Notion | CREATE | New Module",
            data={
                "parent": {"database_id": MODULEDBID},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": f"[{moduleCode}] {title}"}}]
                    }
                },
            },
        )
        
        # Adding stuff to the page
        """res = MakeRequest(
            # Add new Module Page blocks
            "PATCH",
            f"https://api.notion.com/v1/blocks/{modules[moduleCode]['id']}/children",
            "Notion | UPDATE | Add basic blocks",
            data={
                "children": [
                    {
                        "object": "block",
                        "type": "column_list",
                        "column_list": {
                            "children": [
                                {
                                    "object": "block",
                                    "type": "column",
                                    "column": {"children": []},
                                },
                                {
                                    "object": "block",
                                    "type": "column",
                                    "column": {"children": []},
                                },
                            ]
                        },
                    },
                    {"object": "block", "type": "divider", "divider": {}},
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {"text": {"content": "Tutorial / Lab Schedule"}}
                            ],
                            "is_toggleable": True,
                        },
                    },
                ]
            },
        )
        for result in res["results"]:
            if result.get("type") == "column_list":
                ListIDs = result.get("id")
                break
        res = MakeRequest(
            # Get a module's columns
            "Get", f"https://api.notion.com/v1/blocks/{ListIDs}/Children",
            "Notion | READ | Module Columns ")
        ListIDs = []
        for result in res["results"]:
            if result.get("type") == "column":
                ListIDs.append(result.get("id"))
        res = MakeRequest(
            # Setup the first subpage
            "Post", f"https://api.notion.com/v1/pages/",
            "Notion | READ | Module Subpage - Course Syllabus",
            data={
                "parent": {
                    "type": "page_id",
                    "page_id": modules[moduleCode]["id"]
                },
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": "Course Syllabus"
                                }
                            }
                        ]
                    }
                }
            })
        modules[moduleCode]["CourseSyllabusID"] = res["id"]
        res = MakeRequest(
            # Setup the second subpage
            "Post", f"https://api.notion.com/v1/pages/",
            "Notion | READ | Module Subpage - Topics and Objectives",
            data={
                "parent": {
                    "type": "page_id",
                    "page_id": modules[moduleCode]["id"]
                },
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": "Topics and Objectives"
                                }
                            }
                        ]
                    }
                }
            })
        modules[moduleCode]["TopicsObjectivesID"] = res["id"]"""
        
        modules[moduleCode] = MakeRequest(
            # Update Page properties
            "PATCH",
            f"https://api.notion.com/v1/pages/{modules[moduleCode]['id']}",
            "Notion | UPDATE | Page properties",
            data={
                "properties":{
                    "Syllabus Link": {"url": url},
                    "Credits": {"number": int(creds)},
                    "Instructor Email": {"email": teacherEmail},
                    "Instructor Name": {"rich_text": [{"text": {"content": teacher}}]},
                    "Year": {"select": {"name": YEARS[acaYear]}},
                    "Semester": {"multi_select" : [{"name": SEMESTERS[semester]} if semester != "Whole Session" else [{"name": sem} for sem in list(SEMESTERS.keys())]]}
                }
            })
        

    #print(modules["COMP201"])
