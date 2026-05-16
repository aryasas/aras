from core import Aras
from .models import Department, Position, Employee

class DepartmentView(Aras.View):
    model = Department
    title = "Departments"
    icon = "pi pi-sitemap"

class PositionView(Aras.View):
    model = Position
    title = "Positions"
    icon = "pi pi-id-card"

class EmployeeView(Aras.View):
    model = Employee
    title = "Employees"
    icon = "pi pi-users"
