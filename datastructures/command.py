import stormpy as sp
from datastructures.update import Update


# represent a PCFP command (corresponds to jani edge)
class Command:
    # Destination as nested class
    class Destination:
        probability: sp.Expression
        update: Update
        target_loc: object

        def __init__(self, probability, update, location):
            self.probability = probability
            self.update = update
            self.target_loc = location

    _source_loc: object
    _guard: sp.Expression
    _destinations: [Destination]

    def __init__(self, source_loc, guard, destinations):
        self._source_loc = source_loc
        self._guard = guard
        self._destinations = destinations

    def has_destination(self, dest: Destination) -> bool:
        return dest in self._destinations

    @property
    def guard(self) -> sp.Expression:
        return self._guard

    @property
    def source_loc(self):
        return self._source_loc

    @property
    def destinations(self) -> [Destination]:
        return self._destinations
