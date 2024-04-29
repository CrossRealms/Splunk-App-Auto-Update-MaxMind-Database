
import os
import sys


# add lib module to sys path
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        os.path.pardir,
        'lib'
    )
)
