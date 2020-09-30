from locelim.interactive.session import *
from locelim.interactive.commands import *

# hack to print stormpy variables/expressions as we intend
sp.storage.Variable.__repr__ = lambda self: self.name
sp.Expression.__repr__ = lambda self: str(self)
