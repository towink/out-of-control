import logging
import time
from typing import Generator

import stormpy as sp

from locelim.datastructures.pcfp_module import PCFPModule, Location
from locelim.datastructures.config import Config


class PCFPComposition:
    """A parallel composition of various PCFP modules."""

    # private fields with types

    _modules: [PCFPModule]
    _orig_prism: sp.PrismProgram
    _config: Config

    def __init__(self):
        self._modules = []
        self._orig_prism = None
        self._config = Config.default()

    @classmethod
    def from_prism(cls, prism_program: sp.PrismProgram):
        """Creates a composition from a prism program."""
        instance = PCFPComposition()
        # removes all formulas by substituting them, TODO: is this a good idea?
        prism_program = prism_program.substitute_formulas()
        instance._orig_prism = prism_program
        for prism_module in prism_program.modules:
            pcfp_module = PCFPModule.from_prism_module(prism_module)
            instance.add_module(pcfp_module)
        return instance

    def set_config(self, config: Config):
        """Sets the given config in the composition and all submodules."""
        self._config = config
        for module in self._modules:
            module.set_config(config)

    @property
    def expression_manager(self) -> int:
        return self._orig_prism.expression_manager

    @property
    def nr_locations(self) -> int:
        """Total number of locations in all modules of the composition."""
        return sum(module.nr_locations for module in self._modules)

    @property
    def nr_commands(self) -> int:
        """Total number of commands in all modules of the composition."""
        return sum(module.nr_commands for module in self._modules)

    @property
    def nr_transitions(self) -> int:
        """Total number of transitions in all modules of the composition."""
        return sum(module.nr_transitions for module in self._modules)

    @property
    def model_type(self) -> str:
        """Returns the model type (e.g. 'dtmc') as string."""
        if self._orig_prism.model_type == sp.PrismModelType.DTMC:
            return "dtmc"
        elif self._orig_prism.model_type == sp.PrismModelType.MDP:
            return "mdp"
        else:
            raise Exception("model type {} is not supported".format(self._orig_prism.model_type))

    @property
    def undef_constants(self) -> Generator:
        """Generator over undefined constants."""
        for constant in self._orig_prism.constants:
            if not constant.defined:
                yield constant

    @property
    def has_single_module(self) -> bool:
        """Determines whether there is exactly one module in this composition."""
        return len(self._modules) == 1

    def save_as_prism(self, path):
        """Saves the current PCFP composition as a prism file"""
        with open(path, "w") as f:
            f.write(self.to_prism_string())

    def to_prism(self) -> sp.PrismProgram:
        """Converts the PCFP composition to a PRISM program.

        This is the PRISM program parsed from to_prism_string!
        """
        # workaround: export to prism and parse again
        self.save_as_prism("PCFPComposition.to_prism().prism")
        return sp.parse_prism_program("PCFPComposition.to_prism().prism")

    def flatten_composition(self):
        """Flattens this composition into a single PCFP module.

        Uses PrismProgram.flatten()"""
        logging.info(f"flattening {len(self._modules)} modules...")
        t_start = time.time()
        self_as_prism = self.to_prism()
        flattened_prism = self_as_prism.flatten()
        flattened_pcfp_comp = PCFPComposition.from_prism(flattened_prism)
        assert flattened_pcfp_comp.has_single_module
        # remove the action labels, does not happen automatically
        flattened_pcfp_comp._modules[0].remove_all_action_labels()
        flattened_pcfp_comp.set_config(self._config)
        # replace modules
        self._modules = flattened_pcfp_comp._modules
        # also replace original prism, the reason is that the flattened_prism has a new manager
        self._orig_prism = flattened_prism
        t_end = time.time()
        logging.info("...finished flattening, took {:.3f}s".format(t_end-t_start))

    def add_module(self, pcfp_module: PCFPModule):
        """Adds the given PCFP module to this composition."""
        pcfp_module.set_parent_composition(self)
        self._modules.append(pcfp_module)

    def get_module_by_name(self, name: str):
        """Retrieves the requested module by its name."""
        for module in self._modules:
            if module.name == name:
                return module
        raise Exception("no module named {}".format(name))

    def unfold(self, var: sp.Variable):
        """Unfolds the given local variable in the module it belongs to."""
        for module in self._modules:
            if module.has_local_variable(var):
                module.unfold(var)
                return
        raise ValueError("{} is not a local variable of any module".format(var.name))

    def eliminable_locs(self, goal_pred: sp.Expression) -> Generator:
        """Iterates over all eliminable locations in this composition.

        Eliminable locations are those that have no self-loops, and are not initial nor potential goal.
        """
        for module in self._modules:
            yield from module.eliminable_locs(goal_pred)

    def eliminate_loc(self, loc: Location):
        """Eliminates the specified location in the module it belongs to."""
        for module in self._modules:
            if loc in module.locations:
                logging.debug("location {} was found in module {}".format(loc, module.name))
                module.eliminate_loc(loc)
                return
        logging.warning("location {} does not exist".format(loc))

    def remove_unreachable_commands(self):
        """Removes commands that can neve be taken, often needs many SMT calls."""
        for module in self._modules:
            module.remove_unreachable_commands()

    def estimate_elimination_complexity_of_loc(self, loc: Location) -> int:
        for module in self._modules:
            if loc in module.locations:
                return module.estimate_elimination_complexity_of_loc(loc)

    def to_prism_string(self) -> str:
        """Converts this PCFP composition to a prism program (with multiple modules)."""
        res = "\n// generated with PCFPComposition.to_prism_string\n\n"

        # model type
        res += self.model_type + "\n\n"

        # constants
        for const in self._orig_prism.constants:
            if const.type.is_integer:
                type_str = "int"
            elif const.type.is_boolean:
                type_str = "bool"
            elif const.type.is_rational:
                type_str = "double"
            else:
                raise Exception("Unknown variable type")
            if const.defined:
                res += "const {} {} = {};\n".format(type_str, const.name, const.definition)
            else:
                res += "const {} {};\n".format(type_str, const.name)
        res += "\n"

        # global variables
        for global_int in self._orig_prism.global_integer_variables:
            res += "global {}: [{}..{}] init {};\n".format(
                global_int.name,
                global_int.lower_bound_expression,
                global_int.upper_bound_expression,
                global_int.initial_value_expression
            )
        for global_bool in self._orig_prism.global_boolean_variables:
            raise NotImplementedError()
        res += "\n"

        # modules
        for module in self._modules:
            res += module.to_prism_string() + "\n"

        # labels
        for label in self._orig_prism.labels:
            res += "label \"{}\" = {};\n".format(label.name, label.expression)

        return res
