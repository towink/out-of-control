"""Commands intended for interactive use.

A session will be created when this file is loaded.
The "show" functions simply print to the console
but logging may also be enabled for additional info.
"""

from ooc.interactive import Session

# create session when file is included
_session = Session()


def reset_session():
    """Resets the current session,"""
    global _session
    _session = Session()


def session():
    """Returns the current session object, for more advanced use,"""
    res = _session
    return res


def load_model(path_to_prism: str):
    """Loads a prism model."""
    _session.load_model(path_to_prism)


def flatten():
    """Flattens the current PCFP composition into a single module."""
    _session.flatten()


def show_model_constants():
    """Prints the model's definable constants"""
    print(_session.get_model_constants())


def def_model_constants(subst_map):
    """Defines the given constants"""
    _session.def_model_constants(subst_map)


def def_model_constant(name: str, value: object):
    """Defines the given constant"""
    _session.def_model_constant(name, value)


def show_orig_model_info():
    """Prints info about the original built model (not the original prism!)"""
    original_model = _session.build_orig_model()
    print(original_model)  # prints storm's model stats string


def set_property(property: str):
    """Defines the current property for the session"""
    _session.set_property(property)


def check_orig_model():
    """Checks the original model and prints result, constants and property must be defined"""
    num_result = _session.check_orig_model()
    print("result: {} (original model)".format(num_result))


def show_pcfp_stats():
    """Prints stats of current PCFP"""
    for key, value in _session.get_pcfp_stats().items():
        print("{}: {}".format(key, value))


def show_loc_info(max_lines=100):
    """Prints detailed information about each location"""
    # TODO currently does not work
    raise NotImplementedError
    loc_info = _session.get_loc_info()
    counter = 0
    for info in loc_info:
        print(info)
        counter += 1
        if counter >= max_lines:
            print("... {} more lines omitted".format(len(loc_info) - counter))
            break


def eliminate_all():
    """Eliminates all locations according to show_eliminable_locations(), in arbitrary order."""
    _session.eliminate_all()


def eliminate(loc):
    """Eliminates the given location (only works if eliminable)."""
    _session.eliminate(loc)


def remove_unreachable_commands():
    _session.remove_unreachable_commands()


def show_eliminable_locations():
    """Prints the currently eliminable locations with their estimated complexity scores."""
    empty = True
    for loc, score in _session.eliminable_locs():
        print("{}, estimated compl.: {}".format(loc, score))
        empty = False
    if empty:
        print("there are no eliminable locs")


def unfold(var: str):
    """Unfolds the specified variable."""
    _session.unfold(var)


def save_as_prism(path: str):
    _session.save_as_prism(path)


def show_as_prism():
    _session.show_as_prism()
