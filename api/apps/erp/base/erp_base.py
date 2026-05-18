from core import Aras

class ErpBase(Aras.Model):
    __abstract__ = True
    __features__ = ["audit"]
