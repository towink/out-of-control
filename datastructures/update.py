import logging

import stormpy as sp


# assignment occurring in PCFP update
class Assignment:
    lhs: sp.Variable
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


class AtomicUpdate(Update):
    # Set of assignments to be executed in_parallel. At most one assignment to each variable is allowed.
    _par_assignments: [Assignment]

    def __init__(self, asg: Assignment = None):
        self._par_assignments = []
        if asg is not None:
            self._par_assignments.append(asg)

    def add_assignment(self, asg: Assignment):
        self._par_assignments.append(asg)

    def vars_assigned_to(self) -> {sp.Variable}:
        return set(map(lambda asg: asg.lhs, self._par_assignments))

    def rhs_expressions(self) -> {sp.Expression}:
        return set(map(lambda asg: asg.rhs, self._par_assignments))

    def wp(self, postcondition):
        substitutions = {}
        for asg in self._par_assignments:
            substitutions[asg.lhs] = asg.rhs
        return postcondition.substitute(substitutions).simplify()

    def is_idempotent(self):
        # safely approximate idempotency: each variable that is assigned to may not appear nowhere on the right
        vars = self.vars_assigned_to()
        for exp in self.rhs_expressions():
            if exp.contains_variable(vars):  # true iff any of vars appears in exp
                return False
        return True

    def is_nop(self) -> bool:
        return len(self._par_assignments) == 0

    def is_valid(self) -> bool:
        res = True
        if len(self.vars_assigned_to()) != len(self._par_assignments):
            logging.error("variable is assigned more than once in AtomicUpdate")
            res = False
        return res

    def __str__(self):
        return str([str(asg) for asg in self._par_assignments])


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
