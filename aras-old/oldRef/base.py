import typing as t

from abc import ABC
from abc import ABCMeta
from abc import abstractproperty

from .utils import Utilities as ut


class BaseClass:
    """
    Base of all class.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        return

    # def __str__(self):
    #     attrs = ["%s=%s" % (k, v) for (k, v) in self.__dict__.items()]
    #     classname = self.__class__.__name__
    #     return "%s: %s" % (classname, " ".join(attrs))

    def set_attributes(self, *args: t.Any, **kwargs: t.Any):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def print_instance_attributes(self):
        for attribute, value in self.__dict__.items():
            ut.print_param(f"attr | { attribute } =", f"{ value }")
