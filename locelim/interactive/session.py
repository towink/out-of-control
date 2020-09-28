import logging
import time
from typing import Dict

import stormpy as sp

from locelim.datastructures.PCFP import PCFP
from locelim.datastructures.util import primitive_type_to_exp


class Session:
    """Encapsulates an interactive elimination session

    Allows loading a model, setting a property, defining constants, building and checking both the simplified and the
    original model easily. May be used in a terminal or notebook but also in tests etc to reduce boilerplate code.
    """

    # private fields

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

    # private functions

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

    def _get_property_for_prism_model(self, model, define_constants=True):
        # converts the raw user-provided property string to a storm property adapted to specified model
        if self._property is None:
            raise Exception("no property defined")
        if define_constants:
            # define the constants as they may appear in the property
            constant_defs = self._get_constants_for_prism_model(model)
            property_context_model = model.define_constants(constant_defs)
        else:
            property_context_model = model
        properties = sp.parse_properties_for_prism_program(self._property, property_context_model)
        return properties[0]

    def _get_goal_predicate(self) -> sp.Expression:
        # retrieves the goal predicate as an sp.Expression from the given reach property
        if self._property is None:
            raise Exception("cannot infer goal predicate: no property set")
        property = self._get_property_for_prism_model(self._orig_prism_model, define_constants=False)
        # assume property of format "P F exp"
        goal_predicate = property.raw_formula.subformula.subformula.get_expression()
        return goal_predicate

    def _get_simplified_prism_model(self):
        # obtain prism model from the current state of the PCFP
        # stormpy cannot directly parse a prism string, so we write and read from a file
        with open("tmp.prism", "w") as f:
            f.write(self._pcfp.to_prism_string())
        simplified_prism = sp.parse_prism_program("tmp.prism")
        constant_defs = self._get_constants_for_prism_model(simplified_prism)
        simplified_prism_constants_defined = simplified_prism.define_constants(constant_defs)
        return simplified_prism_constants_defined

    # public functions

    def load_model(self, path_to_prism: str):
        """Loads the prism model from the specified path"""
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

    def show_model_constants(self):
        """Prints all undefined constants"""
        print([c.name for c in self._orig_prism_model.constants if not c.defined])

    def def_model_constant(self, name: str, value: object):
        """Defines the specified constant, needed for model building/checking"""
        self._constant_defs[name] = value

    def def_model_constants(self, subst_map):
        """Defines several constants at the same time"""
        for var in subst_map:
            self.def_model_constant(var, subst_map[var])

    def set_property(self, property: str):
        """Sets the reachabilty property given as a string"""
        self._property = property

    def build_orig_model(self):
        """Builds the original model"""
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

    def build_model(self, return_simplified_prism=False):
        """Builds the model for the current PCFP"""
        simplified_prism_constants_defined = self._get_simplified_prism_model()
        if self._property is not None:
            # note that constants are already defined
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

    def check_orig_model(self):
        """Checks the original model

        Requires that a property is set and constants are defined. Prints and returns result.
        """
        model = self.build_orig_model()
        property = self._get_property_for_prism_model(self._orig_prism_model)
        logging.info("start model checking ...")
        t_start = time.time()
        result = sp.model_checking(model, property)
        t_end = time.time()
        logging.info("finished model checking, took {}s".format(t_end - t_start))
        num_result = result.at(model.initial_states[0])
        print("result: {}".format(num_result))
        return num_result

    def check_model(self):
        """Checks the model obtained from the current PCFP.

        Requires that a property is set and constants are defined. Prints and returns result.
        """
        model, simplified_prism = self.build_model(return_simplified_prism=True)
        # constants have already been defined for simplified_prism
        property = self._get_property_for_prism_model(simplified_prism, define_constants=False)
        logging.info("start model checking ...")
        t_start = time.time()
        result = sp.model_checking(model, property)
        t_end = time.time()
        logging.info("finished model checking, took {}s".format(t_end - t_start))
        num_result = result.at(model.initial_states[0])
        print("result: {}".format(num_result))
        return num_result

    def show_orig_model_info(self):
        """Prints storm's statistics string for the original model, requires building"""
        print(self.build_orig_model())

    def unfold(self, var: str):
        """Unfolds the specified variable."""
        self._pcfp.unfold(self._exp_mgr.get_variable(var))

    def eliminate(self, loc: Dict[str, object]):
        """Eliminate specified location (variables encoded as strings)."""
        loc_converted = {}
        for var, value in loc.items():
            var_sp = self._exp_mgr.get_variable(var)
            val_exp = primitive_type_to_exp(value, self._exp_mgr)
            loc_converted[var_sp] = val_exp
        self._pcfp.eliminate_loc(loc_converted, silent=True)

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
        """Print some statistics about the current PCFP"""
        print("number of locatios: {}".format(len(self._pcfp.get_locs())))
        print("number of commands: {}".format(len(self._pcfp.commands)))
        destinations_count = self._pcfp.count_destinations()
        print("number of destinations: {} (avg {}/command)".format(destinations_count,
                                                                   destinations_count / len(self._pcfp.commands)))

    def show_as_prism(self):
        """Prints the current PCFP as prism"""
        print(self._pcfp.to_prism_string())

    def save_as_prism(self, path):
        """Saves the current PCFP as a prism file"""
        with open(path, "w") as f:
            f.write(self._pcfp.to_prism_string())


# Commands intended for interactive use.
# TODO: this is far form being complete

# create a session when this file is included
_session = Session()


def reset_session():
    """Resets the current session"""
    global _session
    _session = Session()


def session():
    """Returns the current session object"""
    return _session


def show_model_constants():
    _session.show_model_constants()


def show_orig_model_info():
    _session.show_orig_model_info()


def set_property(property: str):
    _session.set_property(property)


def load_model(path_to_prism: str):
    _session.load_model(path_to_prism)


def def_model_constant(name: str, value: object):
    _session.def_model_constant(name, value)


def def_model_constants(subst_map):
    _session.def_model_constants(subst_map)


def check_orig_model():
    _session.check_orig_model()


def show_stats():
    _session.show_stats()


def eliminate_all():
    _session.eliminate_all()


def eliminate(loc):
    _session.eliminate(loc)


def show_eliminable_locations():
    _session.show_eliminable_locations()


def show_all_variables():
    raise NotImplementedError


def show_unfoldable_variables():
    raise NotImplementedError


def unfold(var: str):
    _session.unfold(var)


def eliminate_easy_self_loops():
    raise NotImplementedError


def try_eliminate_self_loops(loc=None):
    # applies transition elimination once to each self loop, they may disappear by doing so
    raise NotImplementedError


def save_as_prism(path: str):
    _session.save_as_prism(path)


def show_as_prism():
    _session.show_as_prism()
