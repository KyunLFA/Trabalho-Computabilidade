from dataclasses import dataclass, field

@dataclass
class Transition:
    """Representa uma transição de um autômato de pilha (PDA)."""
    from_state: str
    to_state: str
    read: str              # símbolo da entrada ou epsilon
    pop: str               # topo esperado da pilha (ou ε)
    push: tuple[str, ...]  # sequência a empilhar (vazia = ε)

@dataclass
class Automaton:
    """Representa um autômato de pilha (PDA)."""
    states: set[str]
    input_alphabet: set[str]
    stack_alphabet: set[str]
    initial_state: str
    final_states: set[str]
    transitions: list[Transition] = field(default_factory=list)

    def add_transition(
        self,
        from_state: str,
        to_state: str,
        read: str,
        pop: str,
        push: tuple[str, ...]
    ) -> None:
        """Adiciona uma transição ao autômato.
        
        Args:
            from_state: Estado de origem
            to_state: Estado de destino
            read: Símbolo lido da entrada (ou 'ε')
            pop: Símbolo esperado no topo da pilha (ou 'ε')
            push: Tupla de símbolos a empilhar (tupla vazia para ε)
        """
        transition = Transition(
            from_state=from_state,
            to_state=to_state,
            read=read,
            pop=pop,
            push=push
        )
        self.transitions.append(transition)

    def get_transitions_from(self, state: str) -> list[Transition]:
        """Retorna todas as transições que partem de um dado estado.
        
        Args:
            state: Estado de origem
            
        Returns:
            Lista de transições que partem do estado especificado
        """
        return [t for t in self.transitions if t.from_state == state]