from __future__ import annotations

from typing import Dict

from locelim.datastructures.update import Update

from locelim.datastructures.util import *


# represent a PCFP command (corresponds to jani edge)
class Command:
    # Destination as nested class
    class Destination:
        probability: sp.Expression
        update: Update
        target_loc: {}

        def __init__(self, probability, update, location):
            self.probability = probability
            self.update = update
            self.target_loc = location

        def substitute(self, subst_map):
            result_probability = self.probability.substitute(subst_map).simplify()
            result_update = self.update.substitute(subst_map)
            result_target_loc = {**self.target_loc, **self.update.evaluate(subst_map)}  # merge dicts into new dict
            return Command.Destination(result_probability, result_update, result_target_loc)

        def target_loc_to_prism_string(self) -> str:
            return " & ".join(["({}'={})".format(var.name, str(self.target_loc[var])) for var in self.target_loc])

        def is_equal(self, other: Command.Destination):
            if not are_locs_equal(self.target_loc, other.target_loc):
                return False

            eq: sp.Expression = self.probability.Eq(self.probability, other.probability).simplify()
            if eq.contains_variables():
                return False
            if not eq.evaluate_as_bool():
                return False

            return self.update.is_equal(other.update)

        def to_prism_string(self) -> str:
            if len(self.update._parallel_asgs) > 0 and self.target_loc != {}:
                delimiter = "&"
            else:
                delimiter = ""
            return "{}: {} {} {}".format(
                self.probability,
                self.target_loc_to_prism_string(),
                delimiter,
                self.update.to_prism_string()
            )

        def __str__(self):
            return "{} : {} : {}".format(self.probability, self.update, self.target_loc)

        def __repr__(self):
            return str(self)

    _source_loc: {}
    _guard: sp.Expression
    _destinations: [Destination]

    def __init__(self, source_loc, guard, destinations):
        self._source_loc = source_loc
        self._guard = guard
        self._destinations = destinations

    def has_destination(self, dest: Destination) -> bool:
        return dest in self._destinations

    def count_destinations(self):
        return len(self._destinations)

    # a command has a selfloop if at least one target location equals the source location
    def has_selfloop(self) -> bool:
        return any([are_locs_equal(self._source_loc, dest.target_loc) for dest in self._destinations])

    def has_only_selfloops(self) -> bool:
        # true if all transitions are self loops
        return all([are_locs_equal(self._source_loc, dest.target_loc) for dest in self._destinations])

    def has_nop_selfloop(self) -> bool:
        return any([dest.update.is_nop() for dest in self._destinations])

    def get_nop_selfloops(self) -> [Destination]:
        return [dest.update.is_nop() for dest in self._destinations]

    def substitute(self, subst_map: Dict[sp.Variable, sp.Expression]):
        result_guard = self._guard.substitute(subst_map).simplify()
        result_destinations = [dest.substitute(subst_map) for dest in self._destinations]
        result_source_loc = {**self._source_loc, **subst_map}
        result = Command(result_source_loc, result_guard, result_destinations)
        return result

    def is_guard_false(self):
        return not self._guard.contains_variables() and self._guard.evaluate_as_bool() is False

    def is_equal_except_guard(self, other: Command):
        if not are_locs_equal(self._source_loc, other._source_loc):
            return False
        if len(self._destinations) != len(other._destinations):
            return False
        destinations_matched = len(self._destinations) * [False]
        for self_dest in self._destinations:
            self_dest: Command.Destination

            for i, other_dest in enumerate(other._destinations):
                other_dest: Command.Destination

                if destinations_matched[i]:
                    continue
                if self_dest.is_equal(other_dest):
                    destinations_matched[i] = True
                    break

        if False in destinations_matched:
            return False

        return True

    @property
    def guard(self) -> sp.Expression:
        return self._guard

    @guard.setter
    def guard(self, val: sp.Expression):
        self._guard = val

    @property
    def source_loc(self):
        return self._source_loc

    @property
    def destinations(self) -> [Destination]:
        return self._destinations

    def __str__(self):
        return "{} ---{}--->\t{}".format(self._source_loc, self._guard, str(self._destinations))

    def source_loc_to_prism_string(self) -> str:
        res = ""
        for var in self._source_loc:
            res += "({}={}) & ".format(var.name, str(self._source_loc[var]))
        return res

    def to_prism_string(self) -> str:
        destinations_string = " + \n\t\t".join([dest.to_prism_string() for dest in self._destinations])
        return "[] {} {} -> \n\t\t{};".format(self.source_loc_to_prism_string(), self._guard, destinations_string)
