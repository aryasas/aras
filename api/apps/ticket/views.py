# gemini-flash
from core.base.view import View
from .models import Team, Category, Ticket, TicketMessage

# gemini-flash
class TeamView(View):
    model = Team
    title = "Teams"
    icon = "Users"

# gemini-flash
class CategoryView(View):
    model = Category
    title = "Categories"
    icon = "Tag"

# gemini-flash
class TicketView(View):
    model = Ticket
    title = "Tickets"
    icon = "Ticket"
    
    layout = [
        {"type": "tabs", "tabs": [
            {"title": "Details", "fields": ["subject", "ticket_type", "priority", "status", "category_id", "team_id", "assignee_id", "due_date"]},
            {"title": "Requester", "fields": ["requester_name", "requester_email", "party_id"]},
            {"title": "Notes", "fields": ["description"]},
        ]},
        {"type": "child_table", "resource": "erp_ticket_messages"},
    ]

# gemini-flash
class TicketMessageView(View):
    model = TicketMessage
    title = "Messages"
    icon = "MessageSquare"
