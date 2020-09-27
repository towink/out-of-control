import logging
import time
from typing import Dict

import stormpy as sp

from locelim.datastructures.PCFP import PCFP

# a small hack to print variables/expressions right
sp.storage.Variable.__repr__ = lambda self: self.name
sp.Expression.__repr__ = lambda self: str(self)


class Session:
    # the original prism program
    _orig_prism_model: sp.PrismProgram = None
    # the original jani model converted from prism (possibly flattened)
    _orig_jani_model: sp.JaniModel = None
    # the current pcfp where all operations are applied
    _pcfp: PCFP = None
    # the property string as specified by the user
    _property: str = None
    # the current definitions of the model constants
    _constant_defs = {}
    _exp_mgr: sp.ExpressionManager = None

    def show_model_constants(self):
        print([c.name for c in self._orig_prism_model.constants if not c.defined])

    def def_model_constant(self, name: str, value: object):
        self._constant_defs[name] = value

    def _get_constants_for_prism_model(self, prism_model) -> Dict[sp.Variable, sp.Expression]:
        # makes a constant substitution dict for the given prism from the raw user provided defs
        result = {}
        for constant_string, value in self._constant_defs.items():
            constant = prism_model.get_constant(constant_string).expression_variable
            if type(value) is int:
                result[constant] = prism_model.expression_manager.create_integer(value)
            else:
                raise NotImplementedError
        return result

    def build_orig_model(self):
        constant_defs = self._get_constants_for_prism_model(self._orig_prism_model)
        orig_prism_constants_defined = self._orig_prism_model.define_constants(constant_defs)
        if self._property is not None:
            prop = self._get_property_for_prism_model(orig_prism_constants_defined, define_constants=False)
            logging.info("start building original model ...")
            t_start = time.time()
            model = sp.build_model(orig_prism_constants_defined, [prop])
        else:
            logging.info("start building original model ...")
            t_start = time.time()
            model = sp.build_model(orig_prism_constants_defined)
        t_end = time.time()
        logging.info("finished model building, took {}s".format(t_end - t_start))
        return model

    def _get_simplified_prism_model(self):
        with open("tmp.prism", "w") as f:
            f.write(self._pcfp.to_prism_string())
        simplified_prism = sp.parse_prism_program("tmp.prism")
        constant_defs = self._get_constants_for_prism_model(simplified_prism)
        simplified_prism_constants_defined = simplified_prism.define_constants(constant_defs)
        return simplified_prism_constants_defined

    # build the model from the current pcfp,
    def build_model(self, return_simplified_prism=False):
        simplified_prism_constants_defined = self._get_simplified_prism_model()
        if self._property is not None:
            # constants are already defined
            prop = self._get_property_for_prism_model(simplified_prism_constants_defined, define_constants=False)
            logging.info("start building simplified model ...")
            t_start = time.time()
            model = sp.build_model(simplified_prism_constants_defined, [prop])
        else:
            logging.info("start building simplified model ...")
            t_start = time.time()
            model = sp.build_model(simplified_prism_constants_defined)
        t_end = time.time()
        logging.info("finished model building, took {}s".format(t_end - t_start))
        if return_simplified_prism:
            return model, simplified_prism_constants_defined
        else:
            return model

    def show_orig_model_info(self):
        # this automatically prints the statistics string from storm
        print(self.build_orig_model())

    def load_model(self, path_to_prism: str):
        if self._orig_prism_model is not None:
            raise Exception("another model is already loaded")
        logging.info("parsing prism model {} ...".format(path_to_prism))
        prism_model = sp.parse_prism_program(path_to_prism)
        self._exp_mgr = prism_model.expression_manager
        logging.info("converting prism model to jani ...")
        jani_model, _ = prism_model.to_jani([])
        if len(jani_model.automata) > 1:
            logging.info("model has {} modules, will be flattened".format(len(jani_model.automata)))
            jani_model = jani_model.flatten_composition()
        pcfp = PCFP.from_jani(jani_model)
        self._orig_prism_model = prism_model
        self._orig_jani_model = jani_model
        self._pcfp = pcfp

    def unfold(self, var: str):
        self._pcfp.unfold(self._exp_mgr.get_variable(var))

    def set_property(self, property: str):
        self._property = property

    def _get_property_for_prism_model(self, model, define_constants=True):
        if define_constants:
            # define the constants as they may appear in the property
            constant_defs = self._get_constants_for_prism_model(model)
            property_context_model = model.define_constants(constant_defs)
        else:
            property_context_model = model
        properties = sp.parse_properties_for_prism_program(self._property, property_context_model)
        return properties[0]

    def _get_property_for_orig_prism(self, define_constants=True):
        return self._get_property_for_prism_model(self._orig_prism_model, define_constants)

    # retrieves the goal predicate as an sp.Expression from the given reach property
    def _get_goal_predicate(self) -> sp.Expression:
        if self._property is None:
            raise Exception("cannot infer goal predicate: no property set")
        property = self._get_property_for_prism_model(self._orig_prism_model, define_constants=False)
        goal_predicate = property.raw_formula.subformula.subformula.get_expression()
        return goal_predicate

    def check_orig_model(self):
        if self._property is None:
            raise Exception("cannot check model: no property defined")
        model = self.build_orig_model()
        property = self._get_property_for_prism_model(self._orig_prism_model)
        logging.info("start model checking ...")
        t_start = time.time()
        result = sp.model_checking(model, property)
        t_end = time.time()
        logging.info("finished model checking, took {}s".format(t_end - t_start))
        print(result.at(model.initial_states[0]))

    def check_model(self):
        if self._property is None:
            raise Exception("cannot check model: no property defined")
        model, simplified_prism = self.build_model(return_simplified_prism=True)
        # constants have already been defined for simplified_prism
        property = self._get_property_for_prism_model(simplified_prism, define_constants=False)
        logging.info("start model checking ...")
        t_start = time.time()
        result = sp.model_checking(model, property)
        t_end = time.time()
        logging.info("finished model checking, took {}s".format(t_end - t_start))
        print("result: {}".format(result.at(model.initial_states[0])))

    def eliminate_all(self):
        if self._property is None:
            logging.warning("eliminating without property")
        goal_predicate = self._get_goal_predicate()
        to_eliminate = self._pcfp.get_eliminable_locs(goal_predicate)
        while to_eliminate:
            loc = to_eliminate.pop()
            logging.info("eliminating {}".format(loc))
            t_start = time.time()
            self._pcfp.eliminate_loc(loc, silent=True)
            t_end = time.time()
            logging.info("elimination took {}s".format(t_end - t_start))
            to_eliminate = self._pcfp.get_eliminable_locs(goal_predicate)

    def show_eliminable_locations(self):
        if self._property is None:
            goal_predicate = self._exp_mgr.create_boolean(True)
        else:
            goal_predicate = self._get_goal_predicate()
        print("currently eliminable locations:")
        [print(loc) for loc in self._pcfp.get_eliminable_locs(goal_predicate)]

    def show_stats(self):
        print("number of locatios: {}".format(len(self._pcfp.get_locs())))
        print("number of commands: {}".format(len(self._pcfp.commands)))
        destinations_count = self._pcfp.count_destinations()
        print("number of destinations: {} (avg {}/command)".format(destinations_count,
                                                                   destinations_count / len(self._pcfp.commands)))

    def show_as_prism(self):
        print(self._pcfp.to_prism_string())

    def save_as_prism(self, path):
        with open(path, "w") as f:
            f.write(self._pcfp.to_prism_string())


# print("Welcome to the interactive location elimination. You may type \"show_help()\".")

# the current session
_session = Session()


# for doing hacks
def session():
    return _session


def show_help():
    return "This should list the available commands :)"


def show_model_constants():
    _session.show_model_constants()


def show_orig_model_info():
    _session.show_orig_model_info()


def set_property(property: str):
    _session.set_property(property)


def reset_session():
    # does not work like this
    _session = Session()


def load_model(path_to_prism: str):
    _session.load_model(path_to_prism)


def def_model_constant(name: str, value: object):
    _session.def_model_constant(name, value)


def def_model_constants(subst_map):
    for var in subst_map:
        def_model_constant(var, subst_map[var])


def check_orig_model():
    _session.check_orig_model()


def show_variables():
    _session.show_variables()


# number of commands, number of locations, ...
def show_stats():
    _session.show_stats()


# eliminate as much as possible
def eliminate_all():
    _session.eliminate_all()


# locations that can be immediately eliminated:
# no self loops, definitely not initial or target
def show_eliminable_locations():
    _session.show_eliminable_locations()


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
def try_eliminate_self_loops(loc=None):
    # show how many where eliminated
    pass


def eliminate(loc):
    # fails if loc is not eliminable
    pass


def save_as_prism(path: str):
    pass


def show_as_prism():
    _session.show_as_prism()
