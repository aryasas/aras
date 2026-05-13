from .aras import Aras

class Service(Aras):
    """
    Level 2 Core Service.
    Base category for all stateless logic and utility providers in the framework.
    """
    __abstract__ = True
