from os import environ
from sys import exit
from datetime import datetime
from dotenv import load_dotenv as LoadEnvVariables
from bs4 import BeautifulSoup
import openai
from utils import MakeRequest, GetAcademicYear, NotionURLToID
from base64 import b64encode


# Get Globals
LoadEnvVariables()
OPENAIAPIKEY = environ.get("openaiapikey")
SEMESTERS = {
    "Second Semester" : "Second",
    "First Semester" : "First"
}
client_auth = f"{environ.get('OAUTH_CLIENT_ID')}:{environ.get('OAUTH_CLIENT_SECRET')}"
client_auth = b64encode(client_auth.encode()).decode()


# General Subroutines
def bulletSyllabus(text, chunk_size=2000):
    bullet_text = ""
    with open("prompt.txt", "r") as f:
        prompt = f.read() 
    logmsg = " | Module Access | openai | Convert syllabus into structured bullet points"
    
    client = openai.OpenAI()
    
    # Initialize OpenAI API
    try: 
        completion  = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
        )
        print(f"200" + logmsg)
    except openai.APIStatusError as e: 
        print(f"400" + logmsg)
        print(f"Response Message: {e}")
        exit(1)
    bullet_text = str(completion.choices[0].message.content)

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
            bullet_item = {
                'bulleted_list_item': {
                    'rich_text': [
                        {'text': {'content': content}}
                    ]
                }
            }
            # Adjust the stack based on the current indent level
            while stack and stack[-1][1] >= indent_level:
                stack.pop()
            
            if stack:
                stack[-1][0].append(bullet_item)

            # Add a new stack entry for children if not at max depth
            if indent_level < 4 and content:  # Ensure non-empty content before adding a new list
                new_list = []
                bullet_item['bulleted_list_item']['children'] = new_list
                stack.append((new_list, indent_level))
    
    def clean_empty_children(blocks):
        for block in blocks:
            if 'children' in block['bulleted_list_item'] and not block['bulleted_list_item']['children']:
                del block['bulleted_list_item']['children']  # Remove empty children
            elif 'children' in block['bulleted_list_item']:
                clean_empty_children(block['bulleted_list_item']['children'])  # Recur for nested blocks

    clean_empty_children(root)
    return root

def AcaYearToText(acaYear, startYear):
    year = int(acaYear[2:4]) - int(startYear[2:4]) + 1
    # Handle numbers ending in 11, 12, 13 specially
    if 10 <= year % 100 <= 20:
        suffix = "th"
    else:
        # Look at the last digit
        last_digit = year % 10
        if last_digit == 1:
            suffix = "st"
        elif last_digit == 2:
            suffix = "nd"
        elif last_digit == 3:
            suffix = "rd"
        else:
            suffix = "th"
    return f"{year}{suffix} Year"
        

def ParseModules(modules: list, db, personId):
    for moduleCode in modules:
        moduleInfo = ScrapeModuleInfo(moduleCode)
        person = db.get_table("Person")._Retrieve({"person_id": personId})[0]
        personsNotion = db.get_table("NotionApp")._Retrieve({"person_id": personId})[0]
        # person["homepage"] = NotionURLToID(person["homepage"])
        if not person["modules"]:
            person["modules"] = GetPage("Modules", personsNotion["access_token"], person["homepage"])
        modulePageId = CreateNewModulePage(moduleCode, person["modules"], moduleInfo["title"], personsNotion["access_token"])
        db.get_table("Modules")._Update({"module_notion_id":modulePageId},{"person_id": personId, "module_id": moduleCode})
        PopulateModulePage(modulePageId, moduleInfo["syllabus"], moduleInfo["aims"], moduleInfo['studyTimes'], moduleInfo['url'], moduleInfo['teacher'], moduleInfo['teacherEmail'], moduleInfo['semester'], moduleInfo['credits'], person["start_year"], personsNotion["access_token"])
        if not person["assessments"]:
            person["assessments"] = GetPage('Assessment Material', personsNotion["access_token"], person["homepage"])
        if not person["assignments"]:
            person["assignments"] = GetPage('Assignments and Exams', personsNotion["access_token"], person["homepage"])
        CreateAssessment_AssignmentsPage(modulePageId, person["assignments"], person["assessments"], moduleInfo["assessments"], personsNotion["access_token"])
        if not person["objectives"]:
            person["objectives"] = GetPage('Objectives', personsNotion["access_token"], person["homepage"])
        CreateLoPage(modulePageId, person["objectives"], moduleInfo["los"], personsNotion["access_token"])
        db.get_table("Modules")._Update({
            "pushed": 1,
            "module_notion_id": modulePageId
        },{"person_id": personId, "module_id": moduleCode})
        
def CreateNewModulePage(moduleCode, id, title, accessToken):
    res = MakeRequest(
        "POST",
        f"https://api.notion.com/v1/pages",
        "New Module",
        data={
            "parent": {"database_id": id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": f"[{moduleCode}] {title}"}}]
                }
            },
        },
        headers={
            "Authorization": f"Bearer {accessToken}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
    )
    return res["id"]

def PopulateModulePage(modulePageId, syllabus, aims, studyTimes, url, teacher, teacherEmail, semester, credits, startYear, accessToken):
    MakeRequest( # Setup the Module Information sub-page
        "PATCH", f"https://api.notion.com/v1/blocks/{modulePageId}/children",
        "Module Information Template",
        data={
            "children": [
                {
                    "callout": {
                        "rich_text": [{'text': {"content": 'Unfortunately, Notion API doesn\'t have a way for the program to create Linked Views or apply templates. \nTo use my template in conjunction with this data do the following:\n1. Copy everything\n2. Delete it all \n3. Select the “[COMP] COURSE NAME” template \n4. Paste the data underneath the now loaded template'}}],
                        "icon": {'type': 'emoji', 'emoji': '‼️'}
                    }
                },
                {
                "heading_1": {
                    "rich_text": [
                        {
                        "text": {
                            "content": "Module Information"
                        }
                        }
                    ]
                    }
            }]
        },
        headers={
            "Authorization": f"Bearer {accessToken}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
    )

    MakeRequest( # Write up Syllabus
    "PATCH", f"https://api.notion.com/v1/blocks/{modulePageId}/children",
    "Module Information Template - Syllabus",
    data={
            "children": [{"heading_2": {"rich_text": [{"text": {"content": "Syllabus"}}]}}]
        + bulletstoNotion(bulletSyllabus(syllabus))
        },
        headers={
            "Authorization": f"Bearer {accessToken}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
    )
    
    MakeRequest( # Write up Aims 
    "PATCH", f"https://api.notion.com/v1/blocks/{modulePageId}/children",
    "Module Information Template - Aims",
    data={
            "children": [{"heading_2": {"rich_text": [{"text": {"content": "Aims"}}]}}]
        + [
            {"paragraph": {"rich_text": [{"text": {"content": chunk}}]}}
            for chunk in [aims[i : i + 2000] for i in range(0, len(aims), 2000)] if chunk
        ]
        },
        headers={
            "Authorization": f"Bearer {accessToken}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
    )

    MakeRequest( # Create Study Hours Table
    "PATCH", f"https://api.notion.com/v1/blocks/{modulePageId}/children",
    "Module Information Template - Study Hours",
    data={
            "children": [
            {"heading_2": {"rich_text": [{"text": {"content": "Study Hours"}}]}},
            {
                "table": {
                    "table_width": 2,
                    "has_column_header": True,
                    "has_row_header": True,
                    "children": [
                        {
                            "table_row": {
                                "cells": [
                                    [{"text": {"content": "Type"}}],
                                    [{"text": {"content": "Hours"}}],
                                ]
                            }
                        }
                    ]
                    + [
                        {
                            "table_row": {
                                "cells": [
                                    [{"text": {"content": heading}}],
                                    [{"text": {"content": studyTimes[heading]}}],
                                ]
                            }
                        }
                        for heading in studyTimes
                    ],
                }
            },
        ]
        },
        headers={
            "Authorization": f"Bearer {accessToken}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
    )
    
    MakeRequest( # Create Lab Schedule
    "PATCH", f"https://api.notion.com/v1/blocks/{modulePageId}/children",
    "Module Information Template - Tutorial / Lab Schedule",
    data={
            "children": [
                    {"heading_2": {"rich_text": [{"text": {"content": "Tutorial / Lab Schedule"}}]}},
                    {"paragraph": {"rich_text": [{"text": {"content": "Monday"}}]}},
                    {"paragraph": {"rich_text": [{"text": {"content": "Tuesday"}}]}},
                    {"paragraph": {"rich_text": [{"text": {"content": "Wednesday"}}]}},
                    {"paragraph": {"rich_text": [{"text": {"content": "Thursday"}}]}},
                    {"paragraph": {"rich_text": [{"text": {"content": "Friday"}}]}},
            ]
        },
        headers={
            "Authorization": f"Bearer {accessToken}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
    )

    MakeRequest( # Update Page properties
        "PATCH",
        f"https://api.notion.com/v1/pages/{modulePageId}",
        "Module Page properties",
        data={
            "properties":{
                "Syllabus Link": {"url": url},
                "Credits": {"number": float(credits)},
                "Instructor Email": {"email": teacherEmail},
                "Instructor Name": {"rich_text": [{"text": {"content": teacher}}]},
                "Year": {"rich_text": [{"text": {"content": AcaYearToText(GetAcademicYear(), startYear)}}]},
                "Semester": {"multi_select" : [{"name": SEMESTERS[semester] + " Semester"} if semester != "Whole Session" else [{"name": sem + " Semester"} for sem in list(SEMESTERS.keys())]]}
            }
        },
        headers={
            "Authorization": f"Bearer {accessToken}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
    )

def CreateAssessment_AssignmentsPage(modulePageId, AssignmentsPageID, AssessmentsPageID, assessments, accessToken):
    for index, assessment in enumerate(assessments):
        res = MakeRequest(
            # Create a new Assignment Page
            "POST",
            f"https://api.notion.com/v1/pages",
            f"New Assignment | {index+1}/{len(assessments)}",
            data={
                "parent": {"database_id": AssignmentsPageID},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": assessment["Assessment"] }}]
                    },
                    "Module" : {"relation": [{"id": modulePageId}]},
                    "Task": {"multi_select" : [{"name": assessment["Type"]}]}
                }
            },
            headers={
                "Authorization": f"Bearer {accessToken}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            }
        )
        MakeRequest(
            # Create a new Assessment Page
            "POST",
            f"https://api.notion.com/v1/pages",
            f"New Assessment | {index+1}/{len(assessments)}",
            data={
                "parent": {"database_id": AssessmentsPageID},
                "properties": {
                    "Material": {
                        "title": [{"text": {"content": assessment["Assessment"] }}]
                    },
                    "Module" : {"relation": [{"id": modulePageId}]},
                    "Linked Assignments" : {"relation": [{"id": res['id']}]},
                    "Weighting": {"number": int(assessment["Weighting"])/100}
                }
            },
            headers={
                "Authorization": f"Bearer {accessToken}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            }
        )

def CreateLoPage(modulePageId, ObjectivesPageID, los, accessToken):
    for index, lo in enumerate(los):
        MakeRequest(
            # Create a new Objective Page
            "POST",
            f"https://api.notion.com/v1/pages",
            f"New Objective | {index+1}/{len(los)}",
            data={
                "parent": {"database_id": ObjectivesPageID},
                "properties": {
                    "Objective": {
                        "title": [{"text": {"content": los[lo] }}]
                    },
                    "Module" : {"relation": [{"id": modulePageId}]},
                    "Type": {"select" : {"name": lo[:-1]}},
                    "Number": {"number" :  int(lo[-1])}
                    
                }
            },
            headers={
            "Authorization": f"Bearer {accessToken}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        )

def GetPage(type:str, accessToken, homepageID):
    res = MakeRequest(
        "GET",
        f"https://api.notion.com/v1/blocks/{homepageID}/children",
        "Find Relevant Databases'",
        headers={
            "Authorization": f"Bearer {accessToken}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
    )["results"]
    for block in reversed(res):
        if block.get("type", "") == 'child_database' and block["child_database"]["title"] == type:
            return block["id"]
    # ['Objectives', 'Notes', 'Assignments and Exams', 'Assessment Material', 'Modules', 'Reading List']

def ScrapeModuleInfo(moduleCode: str):
    try:
        int(moduleCode)
        moduleCode = "COMP" + moduleCode
    except:
        pass

    data = {}
    data["acaYear"] = GetAcademicYear()
    data["url"] = f"https://tulip.liv.ac.uk/mods/student/cm_{moduleCode}_{data["acaYear"]}.htm"
    res = MakeRequest("GET", data["url"], "Liverpool's Module Page", raw=True, returnError=True)
    if isinstance(res, Exception) or res.status_code != 200:
        print("Module Page not found: " + moduleCode)
        return
    soup = BeautifulSoup(res.content, 'html.parser')
    tables = soup.find_all('table', align='center')

    for table in tables:
        rows = table.find_all('tr', valign='Top')

        for row in rows:
            headers = row.find_all('td', class_='ddheader')
            cells = row.find_all('td', class_='dddefault')

            if headers and cells:
                headerNo = headers[0].get_text(strip=True)

                if headerNo == "1.":  # Module Title
                    data["title"] = cells[0].get_text(strip=True)

                elif headerNo == "6.":  # Semester
                    data["semester"] = cells[0].get_text(strip=True)

                elif headerNo == "8.":  # Credits
                    data["credits"] = cells[0].get_text(strip=True)

                elif headerNo == "9.":  # Teacher Info
                    teacher_info = cells[0].find_all('td')  # Correcting how teacher info is parsed
                    if len(teacher_info) >= 3:  # Ensure we have enough data
                        data["teacher"] = teacher_info[0].get_text(strip=True)
                        data["teacherEmail"] = teacher_info[2].get_text(strip=True)

                elif headerNo == "14.":  # Study Times
                    study_times = [c.get_text(strip=True) for c in cells]
                    data["studyTimes"] = {
                        "Lectures": study_times[0] if len(study_times) > 0 else '',
                        "Seminars": study_times[1] if len(study_times) > 1 else '',
                        "Tutorials": study_times[2] if len(study_times) > 2 else '',
                        "Lab Practicals": study_times[3] if len(study_times) > 3 else '',
                        "Fieldwork Placement": study_times[4] if len(study_times) > 4 else '',
                        "Other": study_times[5] if len(study_times) > 5 else '',
                        "Total": study_times[6] if len(study_times) > 6 else ''
                    }

                elif headerNo == "15.":  # Private Study
                    if len(cells) >= 2:
                        data["studyTimes"]["Private Study"] = cells[1].get_text(strip=True)


    # Assessment     
    assessment_table = soup.find('td', string='Assessment').find_parent('table')
    data["assessments"] = []
    rows = assessment_table.find_all('tr')
    for i in range(len(rows)):
        cells = rows[i].find_all('td')
        try:
            name = cells[0].get_text(strip=True)
            if len(cells) >= 5 and not any(a["Assessment"] == name for a in data["assessments"]):
                data["assessments"].append({
                    "Assessment": name,
                    "Type": cells[1].get_text(strip=True),
                    "Weighting": int(cells[2].get_text(strip=True))
                })
        except:
            pass

    # Aims
    table = soup.find('td', string='Aims').find_parent('table')
    data["aims"] = table.find_all('tr')[2].contents[3].get_text(strip=True)

    # Learning Objectives
    table = soup.find('td', string='Learning Outcomes').find_parent('table')
    data["los"] = {}
    rows = table.find_all('tr')[2:]  # Exclude header row
    for row in rows:
        cells = row.find_all('td')
        txt = cells[1].text.strip()
        outerBracket = txt.find(")")
        data["los"][txt[1:outerBracket]] = txt[outerBracket+1:].strip()

    # Syllabus
    table = soup.find('td', string='Syllabus').find_parent('table')
    data["syllabus"] = table.find_all('td')[2].contents[1].get_text(strip=True)

    return data
