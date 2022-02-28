# -*- coding: utf-8 -*-

# vexptoolbox: Vizard Toolbox for Behavioral Experiments

__version__ = '0.1'

from .data import *
from .stats import * 

try:
    import viz
    from .experiment import *
    from .vrutil import *
    from .recorder import *
    from .replay import * 
    from .eyeball import *

except ImportError:
    print('Note: vexptoolbox is not running under Vizard, or Vizard packages could not be imported. Only analysis tools will be available.')
