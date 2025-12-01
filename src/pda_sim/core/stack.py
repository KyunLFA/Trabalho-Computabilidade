class Stack:
    """Wrapper sobre list para operações de pilha.

    Operações atômicas úteis para snapshot de estados em simulação de PDA.
    """

    def __init__(self):
        """Inicializa uma pilha vazia."""
        self._items: list[str] = []

    def push(self, seq: tuple[str, ...]) -> None:
        """Empilha uma sequência de símbolos (do último para o primeiro).

        Args:
            seq: Tupla de símbolos a empilhar. O último elemento da tupla
                 ficará no topo da pilha.

        Exemplo:
            >>> stack = Stack()
            >>> stack.push(('X', 'Z'))  # empilha X, depois Z
            >>> stack.peek()
            'Z'  # Z fica no topo
        """
        for symbol in seq:
            self._items.append(symbol)

    def pop(self) -> str:
        """Remove e retorna o símbolo do topo da pilha.

        Returns:
            Símbolo removido do topo

        Raises:
            IndexError: Se a pilha estiver vazia
        """
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> str:
        """Retorna o símbolo do topo sem remover.

        Returns:
            Símbolo do topo da pilha

        Raises:
            IndexError: Se a pilha estiver vazia
        """
        if not self._items:
            raise IndexError("peek from empty stack")
        return self._items[-1]

    def as_str(self) -> str:
        """Retorna representação em string da pilha.

        Returns:
            String com símbolos separados por vírgula, do fundo ao topo.
            Pilha vazia retorna "ε".

        Exemplo:
            >>> stack = Stack()
            >>> stack.push(('X', 'Z'))
            >>> stack.as_str()
            'X,Z'  # X no fundo, Z no topo
        """
        if not self._items:
            return "ε"
        return ",".join(self._items)

    def is_empty(self) -> bool:
        """Verifica se a pilha está vazia.

        Returns:
            True se a pilha estiver vazia, False caso contrário
        """
        return len(self._items) == 0

    def __len__(self) -> int:
        """Retorna o tamanho da pilha."""
        return len(self._items)

    def __repr__(self) -> str:
        """Retorna representação técnica da pilha."""
        return f"Stack({self._items})"

    def copy(self) -> 'Stack':
        """Cria uma cópia profunda da pilha (útil para snapshots).

        Returns:
            Nova instância de Stack com os mesmos elementos
        """
        new_stack = Stack()
        new_stack._items = self._items.copy()
        return new_stack

    def items(self):
        return self._items