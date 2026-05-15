from core import Aras
from .models import Company, Currency, Uom, PriceType

class CompanyView(Aras.View):
    model = Company
    title = "Companies"

class CurrencyView(Aras.View):
    model = Currency
    title = "Currencies"

class UomView(Aras.View):
    model = Uom
    title = "Units of Measure"

class PriceTypeView(Aras.View):
    model = PriceType
    title = "Price Lists"
