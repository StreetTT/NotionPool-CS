from os import getenv
from requests import request, exceptions
from sys import exit
from json import loads
from datetime import datetime as dt
from datetime import timedelta as td
from dotenv import load_dotenv as LoadEnvVariables
from bs4 import BeautifulSoup
import openai


# Get Globals
LoadEnvVariables()
NOTIONTOKEN = getenv("notiontoken")
OPENAIAPIKEY = getenv("openaiapikey")
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
def MakeRequest(method: str, url: str, message: str, data: dict = None, raw: bool = False, returnError: bool = False):
    if data is None:
        res = request(method=method, url=url, headers=HEADERS)
    else:
        res = request(method=method, url=url, json=data, headers=HEADERS)
    print(f"{res.status_code} | {method} | {url.removeprefix("https://").split("/", 1)[0]} | {message}")
    try:
        res.raise_for_status()
        if res.status_code == 200:
            return (res if raw else loads(res.text))
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
    if date.month >= 6:  # If the month is June (6) or later
        start_year = year
        end_year = year + 1
    else:  # If the month is earlier than September
        start_year = year - 1
        end_year = year
    
    # Format the academic year as YYYYYY
    return f"20{start_year % 100:02d}{end_year % 100:02d}"

def bulletSyllabus(text, chunk_size=2000):
    bullet_text = ""
    client = openai.OpenAI(api_key=OPENAIAPIKEY)
    with open("prompt.txt", "r") as f:
        prompt = f.read()
    
    # Initialize OpenAI API
    logmsg = " | Module Access | openai | Convert syllabus into structured bullet points"
    try: 
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            stream=True,
        )
        print(f"200" + logmsg)
    except openai.error.OpenAIError as e: 
        print(f"400" + logmsg)
        print(f"Response Message: {e}")
        exit(1)
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            bullet_text += chunk.choices[0].delta.content
    
    return bullet_text

def bulletstoNotion(text):
    lines = text.strip().split('\n')
    root = []
    stack = [(root, -1)]  # (current_list, current_level)

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue  # Skip empty lines
        
        indent_level = (len(line) - len(stripped_line)) // 4  # assuming 4 spaces per indent level
        content = stripped_line.strip('- ').strip()

        if content:  # Process non-empty content
            bullet_item = {'bulleted_list_item': {'rich_text': [{'text': {'content': content}}]}}
            
            # Adjust the stack based on the current indent level
            while stack and stack[-1][1] >= indent_level:
                stack.pop()
            
            if stack:
                stack[-1][0].append(bullet_item)
                # # another 0

            # Add a new stack entry for children if not at max depth
            if indent_level < 4:
                new_list = []
                bullet_item['bulleted_list_item']['children'] = new_list
                stack.append((new_list, indent_level))
            else:
                bullet_item['bulleted_list_item']['children'] = []

    return root



if __name__ == "__main__":
    modules = {}
    print("Enter Module Numbers: ")
    print("Enter X when done.")
    module = None
    while module != "X":
        module = input().upper()
        try:
            int(module)
            module = "COMP" + module
        except:
            pass
        modules[module] = None
    modules.pop("X")
    print("---")
    for moduleCode in modules:
        # Setting Up the Module Page
        print("---" + moduleCode + "---")
        acaYear = get_academic_year(dt.now())
        url = f"https://tulip.liv.ac.uk/mods/student/cm_{moduleCode}_{acaYear}.htm"
        res = MakeRequest("GET",url,"Liverpool's Module Page",raw=True, returnError=True)
        if isinstance(res, Exception) or res.status_code != 200:
            print("Module Page not found: " + moduleCode)
        else:

            soup = BeautifulSoup(res.content, 'html.parser')
            tables = soup.find_all('table', align='center')
            
            for table in tables:
                rows = table.find_all('tr', valign='Top')
                
                for row in rows:
                    headers = row.find_all('td', class_='ddheader')
                    cells = row.find_all('td', class_='dddefault')

                    if headers and cells and headers[0].get_text(strip=True) in ["1.", "6.", "8.","9.","14.", "15."] :
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
                            studyTimes = {}
                            studyTimes["Lectures"] = cells[0].get_text(strip=True)
                            studyTimes["Seminars"] = cells[1].get_text(strip=True)
                            studyTimes["Tutorials"] = cells[2].get_text(strip=True)
                            studyTimes["Lab Practicals"] = cells[3].get_text(strip=True)
                            studyTimes["Fieldwork Placement"] = cells[4].get_text(strip=True)
                            studyTimes["Other"] = cells[5].get_text(strip=True)

                        elif headerNo == "15.":
                            studyTimes["Private Study"] = cells[1].get_text(strip=True)

            # Assessment     
            table = soup.find('td', string='Assessment').find_parent('table')
            assessments = []
            rows = table.find_all('tr')[5:-1]  # Exclude header row
            for i in range(0,len(rows),2):
                row = rows[i]
                cells = row.find_all('td')
                txt = cells[4].text.strip()
                assessments.append({
                    "Assessment": txt[1:txt.find(")")],
                    "Type": cells[1].text.strip(),
                    "Weighting": int(cells[2].text.strip())
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
            
            
            MODULEDBID = NotionURLToID(getenv("moduleurl"))
            ASSIGNMENTDBID = NotionURLToID(getenv("assignmenturl"))
            ASSESSMENTDBID = NotionURLToID(getenv("assesmenturl"))
            OBJECTIVEDBID = NotionURLToID(getenv("objectiveurl"))

            modules[moduleCode] = MakeRequest(
                # Create a new Module Page
                "POST",
                f"https://api.notion.com/v1/pages",
                "New Module",
                data={
                    "parent": {"database_id": MODULEDBID},
                    "properties": {
                        "Name": {
                            "title": [{"text": {"content": f"[{moduleCode}] {title}"}}]
                        }
                    },
                },
            )
            
            # Adding stuff to Module page
            res = MakeRequest(
                # Setup the Module Information subpage
                "PATCH", f"https://api.notion.com/v1/blocks/{modules[moduleCode]["id"]}/children",
                "Module Information Template",
                data={
                    "children": [{
                        "paragraph": {
                            "rich_text": [
                                {
                                "text": {
                                    "content": "Module Information"
                                }
                                }
                            ]
                            }
                    }]
                }
            )
            res = MakeRequest(
                # Setup the Module Information columns
                "PATCH", f"https://api.notion.com/v1/blocks/{res['results'][0]["id"]}/children",
                "Module Information Template - Columns List",
                data={
                    "children": [{
                        "type": "column_list",
                        "column_list": {
                            "children": [
                                {
                                    "type": "column",
                                    "column": {"children": []},
                                },
                                {
                                    "type": "column",
                                    "column": {"children": []},
                                },
                            ]
                        }
                    }]
                }
            )
            for result in res["results"]:
                if result.get("type") == "column_list":
                    importantIDs = result.get("id")
                    break
            res = MakeRequest(
                # Get a module's columns
                "GET", f"https://api.notion.com/v1/blocks/{importantIDs}/Children",
                "Module Information Template - Columns ")
            importantIDs = []
            for result in res["results"]:
                if result.get("type") == "column":
                    importantIDs.append(result.get("id"))
            
            children = [{
                        "heading_2": {
                            "rich_text": [
                                {
                                "text": {
                                    "content": "Syllabus"
                                }
                                }
                            ]
                            }
                    }] + bulletstoNotion(bulletSyllabus(syllabus)) +  [{
                        "heading_2": {
                            "rich_text": [
                                {
                                "text": {
                                    "content": "Tutorial / Lab Schedule"
                                }
                                }
                            ]
                            }
                    }]
            
            res = MakeRequest(
            # Setup the left column
            "PATCH", f"https://api.notion.com/v1/blocks/{importantIDs[0]}/Children",
            "Module Information Template - Left",
            data={
                    "children": children
                }
            )
            children = [{
                "table_row" : {
                "cells":[[{
                    "text": {
                        "content": "Type"
                    }
                }],[{
                    "text": {
                        "content": "Hours"
                    }
                }]

                ]
            }}]
            children += [{
                "table_row" : {
                "cells":[[{
                    "text": {
                        "content": heading
                    }
                }],[{
                    "text": {
                        "content": studyTimes[heading]
                    }
                }]

                ]
            }} for heading in studyTimes]
            res = MakeRequest(
            # Setup the right column
            "PATCH", f"https://api.notion.com/v1/blocks/{importantIDs[1]}/Children",
            "Module Information Template - Right",
            data={
                    "children": [{
                        "heading_2": {
                            "rich_text": [
                                {
                                "text": {
                                    "content": "Aims"
                                }
                                }
                            ]
                            }
                    }] + [{
                        "paragraph": {
                            "rich_text": [
                                {
                                "text": {
                                    "content": chunk
                                }
                                }
                            ]
                            }
                    } for chunk in [aims[i:i + 2000] for i in range(0, len(aims), 2000)] ] + [{
                        "heading_2": {
                            "rich_text": [
                                {
                                "text": {
                                    "content": "Study Hours"
                                }
                                }
                            ]
                            }
                    },
                    {
                        "table": {
                            "table_width": 2,
                            "has_column_header": True,
                            "has_row_header": True,
                            "children": children
                        }
                    }]
                }
            )
            modules[moduleCode] = MakeRequest(
                # Update Page properties
                "PATCH",
                f"https://api.notion.com/v1/pages/{modules[moduleCode]['id']}",
                "Module Page properties",
                data={
                    "properties":{
                        "Syllabus Link": {"url": url},
                        "Credits": {"number": float(creds)},
                        "Instructor Email": {"email": teacherEmail},
                        "Instructor Name": {"rich_text": [{"text": {"content": teacher}}]},
                        "Year": {"select": {"name": YEARS[acaYear]}},
                        "Semester": {"multi_select" : [{"name": SEMESTERS[semester]} if semester != "Whole Session" else [{"name": sem} for sem in list(SEMESTERS.keys())]]}
                    }
                })
            for index, assessment in enumerate(assessments):
                res = MakeRequest(
                    # Create a new Assignment Page
                    "POST",
                    f"https://api.notion.com/v1/pages",
                    f"New Assignment | {index+1}/{len(assessments)}",
                    data={
                        "parent": {"database_id": ASSIGNMENTDBID},
                        "properties": {
                            "Name": {
                                "title": [{"text": {"content": assessment["Assessment"] }}]
                            },
                            "Module" : {"relation": [{"id": modules[moduleCode]['id']}]},
                            "Task": {"multi_select" : [{"name": assessment["Type"]}]}
                        }
                    }
                )
                MakeRequest(
                    # Create a new Assessment Page
                    "POST",
                    f"https://api.notion.com/v1/pages",
                    f"New Assessment | {index+1}/{len(assessments)}",
                    data={
                        "parent": {"database_id": ASSESSMENTDBID},
                        "properties": {
                            "Material": {
                                "title": [{"text": {"content": assessment["Assessment"] }}]
                            },
                            "Module" : {"relation": [{"id": modules[moduleCode]['id']}]},
                            "Linked Assignments" : {"relation": [{"id": res['id']}]},
                            "Weighting": {"number": int(assessment["Weighting"])/100}
                        }
                    }
                )
            for index, lo in enumerate(los):
                res = MakeRequest(
                    # Create a new Objective Page
                    "POST",
                    f"https://api.notion.com/v1/pages",
                    f"New Objective | {index+1}/{len(los)}",
                    data={
                        "parent": {"database_id": OBJECTIVEDBID},
                        "properties": {
                            "Topic/Objective": {
                                "title": [{"text": {"content": los[lo] }}]
                            },
                            "Module" : {"relation": [{"id": modules[moduleCode]['id']}]},
                            "Type": {"multi_select" : [{"name": lo[:-1]}]},
                            "Number": {"number" :  int(lo[-1])}
                            
                        }
                    }
                )
