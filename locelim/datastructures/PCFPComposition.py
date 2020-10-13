import logging
from typing import Generator

import stormpy as sp

from locelim.datastructures.PCFPModule import PCFPModule, Location

from itertools import chain


class PCFPComposition:
    # private fields with types
    _modules: [PCFPModule]
    _orig_prism: sp.PrismProgram

    def __init__(self):
        self._modules = []
        self._orig_prism = None

    @classmethod
    def from_prism(cls, prism_program: sp.PrismProgram):
        """Creates a composition from a prism program."""
        instance = PCFPComposition()
        instance._orig_prism = prism_program
        # TODO maybe do substituteFormulas in prism_program?
        for prism_module in prism_program.modules:
            pcfp_module = PCFPModule.from_prism_module(prism_module)
            instance.add_module(pcfp_module)
        return instance

    @property
    def expression_manager(self):
        return self._orig_prism.expression_manager

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
    def undef_constants(self):
        for constant in self._orig_prism.constants:
            if not constant.defined:
                yield constant

    def add_module(self, pcfp_module: PCFPModule):
        """Adds the given PCFP module to this composition."""
        pcfp_module.set_parent_composition(self)
        self._modules.append(pcfp_module)

    def get_module_by_name(self, name: str):
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
        for module in self._modules:
            yield from module.eliminable_locs(goal_pred)

    def eliminate_loc(self, loc: Location):
        for module in self._modules:
            if loc in module.locations:
                logging.debug("location {} was found in module {}".format(loc, module.name))
                module.eliminate_loc(loc)
                return
        logging.warning("location {} does not exist".format(loc))

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
