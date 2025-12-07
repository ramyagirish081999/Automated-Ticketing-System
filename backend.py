import json
from dotenv import load_dotenv
import os
import anthropic
from agent import *

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)

PATH = r"F:\Automated_Ticketing_Solution\tickets.json"

def get_response(prompt):
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        temperature=0.0,
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text


prompt_template = """ 
You are an expert ticket resolution analyst. 
Analyze the ticket description and provide the information mentioned in the output structure 

INSTRUCTIONS: 
- Analyze the ticket to summarize the issue type. Provide a confidence score between 0 to 1 for the issue type summarization. 
- Provide the severity of the ticket as HIGH, LOW or MEDIUM. Provide a confidence score between 0 to 1 based on the severity. 
- Mention the affected system from the description. Provide a confidence score between 0 to 1 for the affected system. 

CONSTRAINTS: 
- Do not provide prefix, postfix, preamble or any other comments. 
- Strictly adhere to the provided output structure. 
- Do not modify the enum values (HIGH, LOW, MEDIUM). 
- Provide the response in JSON compatible format. 

INPUT: 
Description: 
{DESCRIPTION}

OUTPUT STRUCTURE: 
{{ 
"issue_type": Concise and Precise explanation of Issue Type in string format,
"issue_type_conf": Confidence Score ranging between 0 to 1,
"severity": Assign values from the options available namely HIGH, LOW or MEDIUM, 
"severity_conf": Confidence Score ranging between 0 to 1, 
"affected_system": Concise and Precise explanation of Affected System Description in string format, 
"affected_system_conf": Confidence Score ranging between 0 to 1 
}} 
"""

def json_updater():
    tickets_json = load_json(PATH)
    # tickets_json = tickets_json[:3]
    for ticket in tickets_json:
        if ticket.get("status") != "open":
            continue

        description = ticket.get("description", "")
        prompt = prompt_template.format(DESCRIPTION=description)
        response = get_response(prompt)

        cleaned_json_response = response.replace("```json", "").replace("```", "").strip()

        parsed_json = json.loads(cleaned_json_response)
        ticket["LLM_Issue_Type"] = parsed_json.get("issue_type")
        ticket["LLM_Issue_Type_Confidence"] = parsed_json.get("issue_type_conf")
        ticket["LLM_Severity"] = parsed_json.get("severity")
        ticket["LLM_Severity_Confidence"] = parsed_json.get("severity_conf")
        ticket["LLM_Affected_System"] = parsed_json.get("affected_system")
        ticket["LLM_Affected_System_Confidence"] = parsed_json.get("affected_system_conf")
        mean = (parsed_json.get("issue_type_conf", 0.0) + parsed_json.get("severity_conf", 0.0)+ parsed_json.get("affected_system_conf", 0.0))/3
        if mean > 0.85:
            ticket["status"] = "Closed"
        else:
            ticket["status"] = "Needs Review"
    write_json("updated_tickets.json", tickets_json)

