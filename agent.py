from dotenv import load_dotenv
import os
from llama_index.llms.anthropic import Anthropic
from pydantic import BaseModel, Field
import json
from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import FunctionAgent
import asyncio

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
llm = Anthropic(api_key=api_key, model="claude-sonnet-4-0")
TICKET_PATH =  r"F:\Automated_Ticketing_Solution\tickets.json"
TICKET_PREFIX = "TICKET-"
TICKET_PADDING = 4

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def get_latest_ticket_id(ticket_details) -> int:
    if not ticket_details:
        return 0
    nums = [t.get("ticket_no") for t in ticket_details]
    return max(nums) if nums else 0


def format_ticket_id(num: int) -> str:
    return f"{TICKET_PREFIX}{num:0{TICKET_PADDING}d}"


def increment_ticket_id(ticket_number: int) -> str:
    latest_num = int(ticket_number.split("-")[-1])
    return format_ticket_id(latest_num + 1)


def load_tickets() -> list:
    """ Load existing tickets from the JSON file.
    """
    return load_json(TICKET_PATH) or []


def create_ticket(description: str = Field("Description of the issue")) -> dict:
    """ Create a support ticket based on the description provided.
    """
    ticket_details = load_json(TICKET_PATH) or []
    latest_ticket_num = get_latest_ticket_id(ticket_details)
    print(f"Latest ticket numeric ID: {latest_ticket_num}")

    new_ticket_no = increment_ticket_id(latest_ticket_num)
    new_ticket = {
        "ticket_no": new_ticket_no,
        "description": description,
        "status": "open"
    }
    ticket_details.append(new_ticket)
    write_json(TICKET_PATH, ticket_details)
    print(f"Created ticket: {new_ticket}")
    return new_ticket


def change_status(ticket_no: str =Field(..., description="The ticket number which needs status change. Format example TICKET-0001"), 
                  new_status: str =Field(..., description="The new status for the ticket")) -> dict:
    """ Change the status of a ticket.
    """
    ticket_details = load_json(TICKET_PATH) or []
    for ticket in ticket_details:
        if ticket.get("ticket_no") == ticket_no:
            ticket["status"] = new_status
            write_json(TICKET_PATH, ticket_details)
            print(f"Changed status of {ticket_no} to {new_status}")
            return f"Changed status of {ticket_no} to {new_status}"
    print(f"Ticket {ticket_no} not found.")
    return f"Unable to find the ticket. {ticket_no}"


def show_pending_tickets_severity(severity: str = Field(None, description="Filter tickets by severity level. Severity can be LOW, MEDIUM, HIGH"),
                                   list_of_tickets: list = Field(None, description="List of tickets to filter")) -> list:
    """ Show all pending tickets, optionally filtered by severity.
    """
    if list_of_tickets is None:
        list_of_tickets = load_tickets()
    tickets_by_severity = []
    for ticket in list_of_tickets:
        if ticket.get("LLM_Severity") == str(severity  ).upper():
            tickets_by_severity.append(ticket)
    print(f"Tickets with severity {severity}: {tickets_by_severity}")
    return tickets_by_severity


def show_tickets_by_status(status: str = Field(None, description="Filter tickets by status. Status can be open, closed, in progress, need review."),
                            list_of_tickets: list = Field(None, description="List of tickets to filter")) -> list:
    """ Show tickets filtered by status.
    """
    if list_of_tickets is None:
        list_of_tickets = load_tickets()
    tickets_by_status = []
    for ticket in list_of_tickets:
        if ticket.get("status") == str(status).lower():
            tickets_by_status.append(ticket)
    print(f"Tickets with status {status}: {tickets_by_status}")
    return tickets_by_status


def send_ticket_list() -> list:
    """ Send the list of all tickets.
    """
    tickets = load_tickets()
    print(f"Sending tickets: {tickets}")
    return tickets


load_status_tool = FunctionTool.from_defaults(load_tickets, name="load_tickets", description="Load all existing tickets from the ticketing system.")
create_ticket_tool = FunctionTool.from_defaults( create_ticket, name="create_ticket", description="Create a new support ticket with the provided description.")
change_status_tool = FunctionTool.from_defaults(change_status, name="change_status", description="Change the status of an existing ticket identified by its ticket number.")
show_pending_tickets_severity_tool = FunctionTool.from_defaults( show_pending_tickets_severity, name="show_pending_tickets_severity", description="Show all pending tickets, optionally filtered by severity.")
show_tickets_by_status_tool = FunctionTool.from_defaults( show_tickets_by_status, name="show_tickets_by_status", description="Show tickets filtered by their status.")
send_ticket_list_tool = FunctionTool.from_defaults(send_ticket_list, name="send_ticket_list", description="Send the list of all tickets in the ticketing system.")


system_prompt = """
You are an AI assistant for a ticketing system. 
You have access to various tools to manage and retrieve information about support tickets. 
Use these tools to assist users with their ticketing needs effectively.

Use the following tools as needed:
1. load_tickets: Load all existing tickets from the ticketing system.
2. create_ticket: Create a new support ticket with the provided description.
3. change_status: Change the status of an existing ticket identified by its ticket number.
4. show_pending_tickets_severity: Show all pending tickets, optionally filtered by severity.
5. show_tickets_by_status: Show tickets filtered by their status.
6. send_ticket_list: Send the list of all tickets in the ticketing system.

You can combine multiple tools to fulfill user requests. 
Always ensure to provide accurate and helpful responses based on the ticket data.
For example, if user wants to check pending high-severity tickets, 
you can first load all tickets and then filter them by severity using the appropriate tools.

"""

agent = FunctionAgent(llm=llm, tools=[
    load_status_tool,create_ticket_tool, change_status_tool, show_pending_tickets_severity_tool,
    show_tickets_by_status_tool, send_ticket_list_tool
],
    system_prompt=system_prompt,)

async def call_agent(query):
    response = await agent.run(query)
    return response
