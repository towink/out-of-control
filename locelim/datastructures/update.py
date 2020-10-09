from __future__ import annotations
import logging
from typing import Dict

import stormpy as sp


# assignment occurring in PCFP update
class Assignment:
    lhs: sp.Variable  # Perhaps it's neater to store a stormpy.variable object here?
    rhs: sp.Expression

    def __init__(self, lhs: sp.Variable, rhs: sp.Expression):
        self.lhs = lhs
        self.rhs = rhs

    # over-approximate a no-operation by checking if lhs = rhs, e.g. x=x
    def is_nop(self) -> bool:
        return self.lhs.get_expression() == self.rhs.simplify()

    def __str__(self):
        return "{} := {}".format(self.lhs.name, str(self.rhs))


# update occurring in PCFP commands, is a set of parallel assignments or a chain of updates
class Update:

    # weakest precondition with respect to the given predicate (postcondition)
    def wp(self, postcondition: sp.Expression) -> sp.Expression:
        raise NotImplementedError

    def apply(self, variable_values: Dict[sp.Variable, sp.Expression]) -> Dict[sp.Variable, sp.Expression]:
        raise NotImplementedError

    # Perhaps this should be named "substitute"?
    def remove_variables(self, substitutions: Dict[sp.Variable, sp.Expression]) -> Update:
        raise NotImplementedError

    def flatten(self):
        raise NotImplementedError

    # an idempotent update can be applied just once instead of n>1 times, e.g. x=3 is idempotent
    def is_idempotent(self) -> bool:
        raise NotImplementedError

    def is_nop(self) -> bool:
        raise NotImplementedError

    # check some invariants, for debugging
    def is_valid(self) -> bool:
        raise NotImplementedError

    def substitute(self, subst_map):
        raise NotImplementedError

    def to_subst_map(self) -> Dict[sp.Variable, sp.Expression]:
        raise NotImplementedError

    def evaluate(self, subst_map):
        raise NotImplementedError


class AtomicUpdate(Update):
    # Set of assignments to be executed in_parallel. At most one assignment to each variable is allowed.
    _parallel_asgs: [Assignment]

    def __init__(self, asg: Assignment = None):
        self._parallel_asgs = []
        if asg is not None:
            self._parallel_asgs.append(asg)

    def add_assignment(self, asg: Assignment):
        self._parallel_asgs.append(asg)

    def vars_assigned_to(self) -> {sp.Variable}:
        return set(map(lambda asg: asg.lhs, self._parallel_asgs))

    def rhs_expressions(self) -> {sp.Expression}:
        return set(map(lambda asg: asg.rhs, self._parallel_asgs))

    def wp(self, postcondition: sp.Expression):
        debug = str(postcondition)
        substitutions = {}
        for asg in self._parallel_asgs:
            substitutions[asg.lhs] = asg.rhs
        res = postcondition.substitute(substitutions).simplify()
        return res

    def apply(self, variable_values: Dict[sp.Variable, sp.Expression]) -> Dict[sp.Variable, sp.Expression]:
        new_values: Dict[sp.Variable, sp.Expression] = dict(variable_values)

        for assignment in self._parallel_asgs:
            if assignment.lhs in variable_values.keys():
                rhs = assignment.rhs
                new_rhs = rhs.substitute(variable_values).simplify()
                new_values[assignment.lhs] = new_rhs

        return new_values

    def remove_variables(self, substitutions: Dict[sp.Variable, sp.Expression]) -> Update:
        new_update = AtomicUpdate()
        for assignment in self._parallel_asgs:
            if assignment.lhs not in substitutions.keys():
                new_rhs = assignment.rhs.substitute(substitutions).simplify()
                new_assignment = Assignment(assignment.lhs, new_rhs)
                new_update._parallel_asgs.append(new_assignment)

        return new_update

    def is_idempotent(self):
        # safely approximate idempotency: each variable that is assigned to may not appear nowhere on the right
        vars = self.vars_assigned_to()
        for exp in self.rhs_expressions():
            if exp.contains_variable(vars):  # true iff any of vars appears in exp
                return False
        return True

    def is_nop(self) -> bool:
        return len(self._parallel_asgs) == 0

    def is_valid(self) -> bool:
        res = True
        if len(self.vars_assigned_to()) != len(self._parallel_asgs):
            logging.error("variable is assigned more than once in AtomicUpdate")
            res = False
        return res

    # substitute variables in all assignments, remove assignments where lhs becomes const
    def substitute(self, subst_map) -> Update:
        result = AtomicUpdate()
        for asg in self._parallel_asgs:
            # check if lhs variable is assigned to, if yes then ignore
            if asg.lhs not in subst_map:
                subst_asg = Assignment(asg.lhs, asg.rhs.substitute(subst_map).simplify())
                result.add_assignment(subst_asg)
        return result

    # converts this update to a dictionary
    def to_subst_map(self) -> Dict[sp.Variable, sp.Expression]:
        return {asg.lhs: asg.rhs for asg in self._parallel_asgs}

    # computes an update that is equivalent to executing this update after the other update
    def after(self, other_update) -> Update:
        other_update_map = other_update.to_subst_map()
        result = AtomicUpdate()
        for asg in other_update._parallel_asgs:
            result.add_assignment(Assignment(asg.lhs, asg.rhs))
        for asg in self._parallel_asgs:
            result[asg.lhs] = asg.rhs.substitute(other_update_map).simplify()
        return result

    def __getitem__(self, lhs: sp.Variable):
        for asg in self._parallel_asgs:
            if asg.lhs == lhs:
                return asg.rhs
        return None

    def __setitem__(self, lhs: sp.Variable, rhs: sp.Expression):
        for asg in self._parallel_asgs:
            if asg.lhs == lhs:
                asg.rhs = rhs
                return
        # lhs variable does not exist
        self._parallel_asgs.append(Assignment(lhs, rhs))

    # evaluations this update for a possibly partial variable valuation
    def evaluate(self, subst_map):
        result = {}
        for var in subst_map:
            rhs = self[var]
            if rhs is not None:
                result[var] = rhs.substitute(subst_map).simplify()
            else:
                result[var] = subst_map[var]
        return result

    def is_equal(self, other: AtomicUpdate):
        self_subst, other_subst = self.to_subst_map(), other.to_subst_map()
        if len(self_subst) != len(other_subst):
            return False
        for var in self_subst:
            if var not in other_subst:
                return False
            self_asg_str, other_asg_str = str(self_subst[var]), str(other_subst[var])
            if self_asg_str != other_asg_str:
                return False
        return True

    def to_prism_string(self) -> str:
        if len(self._parallel_asgs) == 0:
            return "true"
        return " & ".join(["({}'={})".format(asg.lhs.name, str(asg.rhs)) for asg in self._parallel_asgs])

    def __str__(self):
        return str([str(asg) for asg in self._parallel_asgs])


class ChainedUpdate(Update):
    _rightmost: AtomicUpdate
    _rest: Update

    def __init__(self, rest: Update, rightmost: AtomicUpdate):
        self._rest = rest
        self._rightmost = rightmost

    def wp(self, postcondition):
        return self._rest.wp(self._rightmost.wp(postcondition))

    def flatten(self):
        raise NotImplementedError

    def is_valid(self) -> bool:
        return self._rightmost.is_valid() and self._rest.is_valid()

    def is_idempotent(self) -> bool:
        raise NotImplementedError

    def is_nop(self) -> bool:
        raise NotImplementedError
