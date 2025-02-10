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

2. **Clone the Notion Template**:
   Accessible [here](https://bowlyntemplates.notion.site/Uni-Template-77b9720029c64d7ebc078cdde9b7cb14?pvs=4)
   
   The program works with this template. DO NOT change the names of the 6 major databases (Objectives, Notes, Assignments and Exams, Assessment Material, Modules, Reading List) or move them. This WILL NOT work otherwise.


3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` File**:
   Create a `.env` file in the project directory and add the following environment variables:
   ```
   OPENAI_API_KEY=<your_openai_key>
   OAUTH_CLIENT_ID=<your_notion_integrations_client_id>
   OAUTH_CLIENT_SECRET=<your_notion_integrations_client_secret>
   NOTION_AUTH_URL=<your_notion_integrations_auth_url>
   FLASK_KEY=<anything_you_want>
   ```

## Usage

1. **Run the Script**:
   Execute the script to start the automation process:
   ```bash
   python main.py
   ```

2. **Input Module Codes**:
   Enter module codes without the "COMP" prefix.

3. **Script Execution**:
   The script will:
   - Fetch module information from the UoL website.
   - Parse and structure the data.
   - Populate and update Notion pages with the gathered information.

## Notes

- Ensure that your Notion API token and database URLs are correctly configured in the `.env` file.
- The script assumes a specific HTML structure from the University of Liverpool's website. If the structure changes, you may need to adjust the HTML parsing logic.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

For any issues or feature requests, please open an issue in the repository or contact the author.


