from collections import Counter as _Counter
from typing import Counter as CounterType
from typing import Generic, TypeVar


class AbortCommand(Exception):
    pass


CounterKey = TypeVar("CounterKey")


class Counter(Generic[CounterKey]):
    def __init__(self):
        self._counter: CounterType[CounterKey] = _Counter()

    def incr(self, key: CounterKey):
        self._counter[key] += 1

    def get(self, key: CounterKey):
        return self._counter[key]


__all__ = (
    "AbortCommand",
    "Counter",
)
