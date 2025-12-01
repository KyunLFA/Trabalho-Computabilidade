from typing import List, Tuple

class Stack:
    def __init__(self, initial: List[str] | None = None):
        self._items: List[str] = list(initial) if initial else []

    def push(self, seq: Tuple[str, ...] | List[str]) -> None:
        # push sequence so that last element becomes top
        for symbol in seq:
            self._items.append(symbol)

    def pop(self) -> str:
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> str:
        if not self._items:
            raise IndexError("peek from empty stack")
        return self._items[-1]

    def as_str(self) -> str:
        if not self._items:
            return "ε"
        # represent from bottom .. top
        return ",".join(self._items)

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def __len__(self):
        return len(self._items)

    def copy(self) -> 'Stack':
        return Stack(initial=self._items.copy())

    def items(self):
        return self._items
