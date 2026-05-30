import warnings
warnings.warn("apps.asset moved to apps.accounting.assets", DeprecationWarning)
from apps.accounting.assets.models import *  # noqa
from apps.accounting.assets.app import *  # noqa
