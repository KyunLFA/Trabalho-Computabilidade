from dataclasses import dataclass, field
from .stack import Stack

@dataclass
class PDAConfig:
    """Snapshot de execução de um autômato de pilha (PDA).

    Representa o estado completo da computação em um determinado momento,
    incluindo estado atual, entrada restante, pilha e histórico de transições.
    Útil para simulação passo-a-passo e exploração de ramos não-determinísticos.
    """

    state: str
    """Estado atual do autômato."""

    remaining_input: list[str]
    """Símbolos da entrada que ainda não foram consumidos."""

    stack: Stack
    """Estado atual da pilha."""

    history: list[str] = field(default_factory=list)
    """Histórico opcional de transições aplicadas (para debug/visualização)."""

    def copy(self) -> 'PDAConfig':
        """Cria uma cópia profunda da configuração.

        Essencial para explorar múltiplos ramos em autômatos não-determinísticos,
        permitindo backtracking sem afetar outras configurações.

        Returns:
            Nova instância de PDAConfig com cópias independentes de todos os campos
        """
        return PDAConfig(
            state=self.state,
            remaining_input=self.remaining_input.copy(),
            stack=self.stack.copy(),
            history=self.history.copy()
        )

    def add_history(self, description: str) -> None:
        """Adiciona uma entrada ao histórico de transições.

        Args:
            description: Descrição da transição aplicada
        """
        self.history.append(description)

    def get_current_input_symbol(self) -> str | None:
        """Retorna o próximo símbolo da entrada sem consumi-lo.

        Returns:
            Próximo símbolo da entrada, ou None se a entrada estiver vazia
        """
        if not self.remaining_input:
            return None
        return self.remaining_input[0]

    def consume_input(self) -> str:
        """Consome e retorna o próximo símbolo da entrada.

        Returns:
            Símbolo consumido

        Raises:
            IndexError: Se não houver mais entrada para consumir
        """
        if not self.remaining_input:
            raise IndexError("No input left to consume")
        return self.remaining_input.pop(0)

    def is_input_empty(self) -> bool:
        """Verifica se toda a entrada foi consumida.

        Returns:
            True se não há mais entrada, False caso contrário
        """
        return len(self.remaining_input) == 0

    def __str__(self) -> str:
        """Retorna representação legível da configuração."""
        inp = "".join(self.remaining_input) if self.remaining_input else "ε"
        return (
            f"Estado: {self.state} | "
            f"Entrada: {inp} | "
            f"Pilha: {self.stack.as_str()}"
        )

    def __repr__(self) -> str:
        """Retorna representação técnica da configuração."""
        return (
            f"PDAConfig(state={self.state!r}, "
            f"remaining_input={self.remaining_input!r}, "
            f"stack={self.stack!r}, "
            f"history={len(self.history)} entries)"
        )