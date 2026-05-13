from .aras import Aras

class Router(Aras):
    """
    Level 2 Core Router.
    Base category for API routing and route factories.
    """
    __abstract__ = True
