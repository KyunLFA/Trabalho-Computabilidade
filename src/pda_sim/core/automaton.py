from dataclasses import dataclass, field
from typing import Tuple, List, Set

@dataclass
class Transition:
    from_state: str
    to_state: str
    read: str              # symbol, 'ε' or '?'
    pop: str               # symbol, 'ε' or '?'
    push: Tuple[str, ...]  # tuple empty means ε

@dataclass
class Automaton:
    states: Set[str]
    input_alphabet: Set[str]
    stack_alphabet: Set[str]
    initial_state: str
    final_states: Set[str]
    transitions: List[Transition] = field(default_factory=list)
    initial_stack_symbol: str = None
    automaton_type: str = "pda"   # "pda" or "dfa"

    def add_transition(self, from_state: str, to_state: str, read: str, pop: str, push: Tuple[str, ...]):
        self.transitions.append(Transition(from_state, to_state, read, pop, push))

    def get_transitions_from(self, state: str):
        return [t for t in self.transitions if t.from_state == state]
