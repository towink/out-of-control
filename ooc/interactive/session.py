import logging
import os
import time
from typing import Dict, Generator

import stormpy as sp

from ooc.datastructures.pcfp_module import PCFPModule
from ooc.datastructures.pcfp_composition import PCFPComposition
from ooc.datastructures.pcfp_module import Location
from ooc.datastructures.config import Config
from ooc.datastructures.util import primitive_type_to_exp, are_locs_equal



class Session:
    """Encapsulates an interactive elimination session

    Allows loading a model, setting a property, defining constants, building and checking both the simplified and the
    original model easily. May be used in a terminal or notebook but also in tests etc to reduce boilerplate code.
    """

    # private fields

    # the original prism program
    _orig_prism_model: sp.PrismProgram
    # the current pcfp where all operations are applied
    _pcfp_composition: PCFPComposition
    # the property string as specified by the user
    _property: str = None
    # the current definitions of the model constants
    _constant_defs = {}

    def __init__(self):
        self._orig_prism_model = None
        self._pcfp = None
        self._property = None
        self._constant_defs = {}

    # private functions

    def _exp_mgr(self) -> sp.ExpressionManager:
        return self._pcfp_composition.expression_manager

    def _get_constants_for_prism_model(self, prism_model) -> Dict[sp.Variable, sp.Expression]:
        # makes a constant substitution dict for the given prism from the raw user provided defs
        result = {}
        for constant_string, value in self._constant_defs.items():
            constant = prism_model.get_constant(constant_string).expression_variable
            if type(value) is int:
                result[constant] = prism_model.expression_manager.create_integer(value)
            elif type(value) is bool:
                result[constant] = prism_model.expression_manager.create_boolean(value)
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
            f.write(self._pcfp_composition.to_prism_string())
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
        pcfp_composition = PCFPComposition.from_prism(prism_model)
        self._orig_prism_model = prism_model
        self._pcfp_composition = pcfp_composition

    def flatten(self):
        """Flattens the current composition into a single module."""
        self._pcfp_composition.flatten_composition()

    def set_config(self, config: Config):
        self._pcfp_composition.set_config(config)

    def get_model_constants(self):
        """Returns all undefined constants"""
        return [c.name for c in self._orig_prism_model.constants if not c.defined]

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

    def build_orig_model(self, return_time=False, symbolic=False):
        """Builds the original model"""
        constant_defs = self._get_constants_for_prism_model(self._orig_prism_model)
        orig_prism_constants_defined = self._orig_prism_model.define_constants(constant_defs)
        if self._property is not None:
            prop = self._get_property_for_prism_model(orig_prism_constants_defined, define_constants=False)
            logging.info("start building original model ...")
            t_start = time.time()
            if symbolic:
                model = sp.build_symbolic_model(orig_prism_constants_defined, [prop])
            else:
                model = sp.build_model(orig_prism_constants_defined, [prop])
        else:
            logging.info("start building original model ...")
            t_start = time.time()
            if symbolic:
                model = sp.build_symbolic_model(orig_prism_constants_defined)
            else:
                model = sp.build_model(orig_prism_constants_defined)
        t_end = time.time()
        logging.info("finished model building, took {}s".format(t_end - t_start))
        if return_time:
            return model, t_end - t_start
        else:
            return model

    def build_model(self, return_time=False, return_simplified_prism=False, symbolic=False):
        """Builds the model for the current PCFP"""
        simplified_prism_constants_defined = self._get_simplified_prism_model()
        if self._property is not None:
            # note that constants are already defined
            prop = self._get_property_for_prism_model(simplified_prism_constants_defined, define_constants=False)
            logging.info("start building simplified model ...")
            t_start = time.time()
            if symbolic:
                model = sp.build_symbolic_model(simplified_prism_constants_defined, [prop])
            else:
                model = sp.build_model(simplified_prism_constants_defined, [prop])
        else:
            logging.info("start building simplified model ...")
            t_start = time.time()
            if symbolic:
                model = sp.build_symbolic_model(simplified_prism_constants_defined)
            else:
                model = sp.build_model(simplified_prism_constants_defined)
        t_end = time.time()
        logging.info("finished model building, took {}s".format(t_end - t_start))
        if return_simplified_prism:
            if return_time:
                return model, t_end - t_start, simplified_prism_constants_defined
            else:
                return model, simplified_prism_constants_defined
        else:
            if return_time:
                return model, t_end - t_start
            else:
                return model

    def check_orig_model(self, return_time=False):
        """Checks the original model

        Returns the result and optionally the model checking time.
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
        if return_time:
            return num_result, t_end - t_start
        else:
            return num_result

    def check_model(self, return_time=False):
        """Checks the model obtained from the current PCFP.

        Returns the result and optionally the model checking time.
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
        if return_time:
            return num_result, t_end - t_start
        else:
            return num_result

    def check_model_exactly(self):
        storm_path = '~/storm/build/bin/storm'
        logging.warning(f'assuming storm path is {storm_path}')
        self._pcfp_composition.save_as_prism("storm_exact_input.prism")

        def constants_string():
            return ",".join(f"{const}={val}" for const, val in self._constant_defs.items())

        command = f"{storm_path} --prism storm_exact_input.prism --constants {constants_string()} --prop '{self._property}' --exact --explchecks"
        os.system(command)

    def unfold(self, var: str):
        """Unfolds the specified variable."""
        self._pcfp_composition.unfold(self._exp_mgr().get_variable(var))

    def eliminate(self, raw_loc: Dict[str, object]):
        """Eliminate specified location (variables encoded as strings)."""
        loc_converted = Location()
        for var, value in raw_loc.items():
            var_sp = self._exp_mgr().get_variable(var)
            val_exp = primitive_type_to_exp(value, self._exp_mgr())
            # loc_converted.val_map[var_sp] = val_exp
            loc_converted = loc_converted.extend({var_sp: val_exp})
        self._pcfp_composition.eliminate_loc(loc_converted)

    def eliminate_all(self, max=None):
        """eliminates all eliminable locs in the composition, in an arbitrary order"""
        if self._property is None:
            logging.warning("eliminating without property")
        goal_predicate = self._get_goal_predicate()
        # get an arbitrary eliminable loc
        loc_to_eliminate = next(self._pcfp_composition.eliminable_locs(goal_predicate), None)
        count = 0
        if max is None:
            max = 10 ** 10
        while loc_to_eliminate and count < max:
            self._pcfp_composition.eliminate_loc(loc_to_eliminate)
            count += 1
            loc_to_eliminate = next(self._pcfp_composition.eliminable_locs(goal_predicate), None)

    def remove_unreachable_commands(self):
        """Eliminates all commands in the current composition that are guaranteed to be never taken."""
        self._pcfp_composition.remove_unreachable_commands()

    def get_loc_info(self):
        """Returns detailed information for each location"""
        # TODO currently does not work
        raise NotImplementedError
        result = []
        for loc in self._pcfp.get_locs():
            commands = self._pcfp.get_commands_with_source(loc)
            # commands_with_selfloops = [cmd for cmd in commands if cmd.has_selfloop()]
            dest_count = sum([len(cmd.destinations) for cmd in commands])
            ingoing = self._pcfp.get_destinations_with_target(loc)
            selfloops = []
            for cmd in commands:
                for dest in cmd.destinations:
                    if are_locs_equal(dest.target_loc, loc):
                        selfloops.append(dest)
            result.append({
                "label": loc,
                "commands": len(commands),
                "trans out": dest_count,
                "trans in": len(ingoing),
                "selfloops": len(selfloops)
            })
        return result

    def eliminable_locs(self) -> Generator:
        """Yields the currently directly eliminable locations.

        A location counts as eliminable if the following three conditions holds:
        - the location has no self-loop
        - it is guaranteed to be neither initial nor final
        Note that eliminating one of these locations can make the others non-eliminable!
        """
        if self._property is None:
            goal_predicate = self._exp_mgr().create_boolean(True)
        else:
            goal_predicate = self._get_goal_predicate()
        for loc in self._pcfp_composition.eliminable_locs(goal_predicate):
            yield loc, self._pcfp_composition.estimate_elimination_complexity_of_loc(loc)

    def get_pcfp_stats(self):
        """Return some statistics about the current PCFP"""
        return {
            "locations": self._pcfp_composition.nr_locations,
            "commands": self._pcfp_composition.nr_commands,
            "transitions": self._pcfp_composition.nr_transitions
        }

    def show_as_prism(self):
        """Prints the current PCFP as prism"""
        print(self._pcfp_composition.to_prism_string())

    def save_as_prism(self, path):
        """Saves the current PCFP as a prism file"""
        with open(path, "w") as f:
            f.write(self._pcfp.to_prism_string())
