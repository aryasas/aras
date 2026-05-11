from arasCore.arasgen import ArasGen

class AccAccountView(ArasGen.View):
    __model__ = "AccAccount"
    __title__ = "Chart of Accounts"
    __icon__ = "fa-sitemap"
    __menu_order__ = 1
    __display_fields__ = ("code", "name")
