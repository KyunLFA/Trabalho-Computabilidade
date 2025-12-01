from dataclasses import dataclass, field
from .stack import Stack
from typing import List

@dataclass
class PDAConfig:
    state: str
    remaining_input: List[str]
    stack: Stack
    history: List[str] = field(default_factory=list)

    def copy(self) -> 'PDAConfig':
        return PDAConfig(
            state=self.state,
            remaining_input=self.remaining_input.copy(),
            stack=self.stack.copy(),
            history=self.history.copy()
        )

    def add_history(self, text: str):
        self.history.append(text)

    def get_current_input_symbol(self):
        if not self.remaining_input:
            return None
        return self.remaining_input[0]

    def consume_input(self):
        if not self.remaining_input:
            raise IndexError("No input left")
        return self.remaining_input.pop(0)

    def is_input_empty(self):
        return len(self.remaining_input) == 0

    def __str__(self):
        inp = "".join(self.remaining_input) if self.remaining_input else "ε"
        return f"Estado: {self.state} | Entrada: {inp} | Pilha: {self.stack.as_str()}"
