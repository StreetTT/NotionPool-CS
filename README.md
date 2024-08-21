# NotionPool-CS

## Overview

This script automates the process of setting up and organizing module information for CS students of the University of Liverpool into a Notion page by fetching data from the TULIP system. It integrates various APIs, including Notion and OpenAI. 

## Features

- **Fetch Module Data**: Retrieve module information from the University of Liverpool's website.
- **Convert Syllabus**: Use OpenAI to structure syllabus text into bullet points.
- **Populate Notion Pages**: Create and update Notion pages with module details, including syllabus, assessments, aims, and learning objectives.
- **Error Handling**: Provides error messages and exits the script if data retrieval fails.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` File**:
   Create a `.env` file in the project directory and add the following environment variables:
   ```
   notiontoken=<your_notion_token>
   openaiapikey=<your_openai_api_key>
   moduleurl=<your_notion_module_db_url>
   assignmenturl=<your_notion_assignment_db_url>
   assesmenturl=<your_notion_assessment_db_url>
   objectiveurl=<your_notion_objective_db_url>
   ```

## Usage

1. **Run the Script**:
   Execute the script to start the automation process:
   ```bash
   python main.py
   ```

2. **Input Module Codes**:
   Enter module codes one by one. Type `X` when done.

3. **Script Execution**:
   The script will:
   - Fetch module information from the UoL website.
   - Parse and structure the data.
   - Populate and update Notion pages with the gathered information.

## Notes

- Ensure that your Notion API token and database URLs are correctly configured in the `.env` file.
- The script assumes a specific HTML structure from the University of Liverpool's website. If the structure changes, you may need to adjust the HTML parsing logic.
- This script is currently tailored to work with my personal Notion setup and the specific structure of the University of Liverpool's module database. I plan to release a public template and version of this script that will be more generic and configurable, allowing others to adapt it to their own Notion setups. 

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

For any issues or feature requests, please open an issue in the repository or contact the author.


