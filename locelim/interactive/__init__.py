import stormpy as sp

from locelim.datastructures.PCFP import PCFP


class Session:
    _prism_model: sp.PrismProgram = None
    _jani_model: sp.JaniModel = None
    _pcfp: PCFP = None
    _property = None

    def load_model(self, path_to_prism: str):
        if self._prism_model is not None:
            print("please reset session before loading new model")
            return
        prism_model = sp.parse_prism_program(path_to_prism)
        jani_model, _ = prism_model.to_jani([])
        if len(jani_model.automata) > 1:
            print("model has several modules, will be flattened")
            jani_model = jani_model.flatten_composition()
        pcfp = PCFP.from_jani(jani_model)
        self._prism_model = prism_model
        self._jani_model = jani_model
        self._pcfp = pcfp

    def unfold(self, var: str):
        pass

    def set_property(self, property: str):
        pass


print("Welcome to the interactive location elimination. You may type \"show_help()\".")

# the current session
_session = Session()


def show_help():
    return "This should list the available commands :)"


def reset_session():
    # does not work like this
    _session = Session()


def load_model(path_to_prism: str):
    _session.load_model(path_to_prism)


def set_property(property: str):
    pass


def define_constant(name: str, value):
    pass


def define_constants(subst_map):
    for var in subst_map:
        define_constant(var, subst_map[var])


# number of commands, number of locations, ...
def show_stats():
    pass


# locations that can be immediately eliminated:
# no self loops, definitely not initial or target
def show_eliminable_locations():
    pass


# all variables that currently exist
def show_all_variables():
    pass


# show all (undefined?) constants
def show_constants():
    pass


def show_commands():
    pass


# variables that can be immediately unfolded, also show their domains
def show_unfoldable_variables():
    pass


def unfold(var: str):
    _session.unfold(var)


# eliminates all easy self loops
def eliminate_easy_self_loops():
    # show how many were eliminated
    pass


# applies transition elimination once to each self loop, they may disappear by doing so
def try_eliminate_self_loops(loc = None):
    # show how many where eliminated
    pass


def eliminate(loc):
    # fails if loc is not eliminable
    pass


# eliminate all eliminable
def eliminate_all():
    pass


def write_prism(path: str):
    pass

