# Out of Control:  Reducing Probabilistic Models by Control-State Elimination

Relieve your probabilistic model checker: Simplify your input model! This projects help you to do so.

## Dependencies
* storm
* stormpy
* networkx

## Usage

```python
# Use this import to start your simplification session!
from ooc.interactive import *

# Load a model and fix a property.
load_model("ooc/models/model_files/coupon.10-1.prism")
set_property("P=? [ F c0 & c1 & c2 & c3 & c4 & c5 & c6 & c7 & c8 & c9 & s=2]")

# Note: If there are undefined constants in the model (probabilities, variable bounds, etc.),
#       then you can just leave them, the simplification will be correct in any case!

# Unfold a variable into the control flow graph.
unfold("s")

# Inspect the control-flow locations that are ready for elimination. 
show_eliminable_locations()

# Remove them all!
eliminate_all()

# Do it with another variable.
unfold("draw")
eliminate_all()

# Get your simplified PRISM file.
show_as_prism()
```
