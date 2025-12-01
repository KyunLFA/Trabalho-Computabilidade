"""Simulador de autômato de pilha (PDA) com suporte a não-determinismo.

Este módulo implementa a lógica central de simulação, incluindo:
- Aplicação de transições individuais
- Execução passo-a-passo com frontier de configurações
- Verificação de aceitação com trace de execução
"""

from typing import Iterator, Optional
from .config import PDAConfig
from .stack import Stack
from .automaton import Automaton, Transition


# Limites de segurança para evitar explosão do espaço de busca
DEFAULT_MAX_STEPS = 1000
DEFAULT_MAX_CONFIGS = 500


def simulate_step(config: PDAConfig, automaton: Automaton) -> list[PDAConfig]:
    """Aplica todas as transições aplicáveis a partir de uma configuração.

    Retorna uma lista de novas configurações (possivelmente vazia se nenhuma
    transição for aplicável). Suporta não-determinismo retornando múltiplas
    configurações quando múltiplas transições são aplicáveis.

    Args:
        config: Configuração atual da execução
        automaton: Autômato sendo simulado

    Returns:
        Lista de novas configurações resultantes das transições aplicáveis.
        Lista vazia se nenhuma transição puder ser aplicada.
    """
    next_configs = []
    current_input_symbol = config.get_current_input_symbol()

    # Obter topo da pilha (ou None se vazia)
    try:
        stack_top = config.stack.peek()
    except IndexError:
        stack_top = None

    # Buscar todas as transições do estado atual
    transitions = automaton.get_transitions_from(config.state)

    for transition in transitions:
        # Verificar se a transição é aplicável
        if not _is_transition_applicable(
                transition,
                current_input_symbol,
                stack_top
        ):
            continue

        # Aplicar a transição criando uma nova configuração
        new_config = _apply_transition(config, transition)
        next_configs.append(new_config)

    return next_configs


def _is_transition_applicable(
        transition: Transition,
        current_input: Optional[str],
        stack_top: Optional[str]
) -> bool:
    """Verifica se uma transição pode ser aplicada no contexto atual.

    Args:
        transition: Transição a verificar
        current_input: Símbolo atual da entrada (None se entrada vazia)
        stack_top: Topo da pilha (None se pilha vazia)

    Returns:
        True se a transição pode ser aplicada, False caso contrário
    """
    # Verificar símbolo de leitura
    if transition.read == 'ε':
        # Transição epsilon não consome entrada (sempre OK quanto à entrada)
        pass
    elif transition.read == '?' and current_input is None:
        pass
    elif current_input is None:
        # Transição requer leitura mas não há entrada
        return False
    elif transition.read != current_input:
        # Símbolo lido não corresponde ao esperado
        return False

    # Verificar topo da pilha
    if transition.pop == 'ε':
        # Transição não requer pop (sempre OK quanto à pilha)
        pass
    elif transition.pop == '?' and stack_top is None:
        pass
    elif stack_top is None:
        # Transição requer pop mas pilha está vazia
        return False
    elif transition.pop != stack_top:
        # Topo da pilha não corresponde ao esperado
        return False

    return True


def _apply_transition(config: PDAConfig, transition: Transition) -> PDAConfig:
    """Aplica uma transição a uma configuração, criando nova configuração.

    Args:
        config: Configuração original
        transition: Transição a aplicar

    Returns:
        Nova configuração resultante da aplicação da transição
    """
    # Copiar configuração para não modificar a original
    new_config = config.copy()

    # Atualizar estado
    new_config.state = transition.to_state

    # Consumir entrada se necessário
    if not transition.read in ['ε', '?']:
        new_config.consume_input()

    # Fazer pop da pilha se necessário
    if transition.pop != 'ε':
        popped = new_config.stack.pop()
    else:
        popped = None

    # Fazer push na pilha se necessário
    if transition.push:  # Se não for tupla vazia
        new_config.stack.push(transition.push)

    # Adicionar ao histórico
    read_str = transition.read
    pop_str = transition.pop
    push_str = ','.join(transition.push) if transition.push else 'ε'

    history_entry = (
        f"{transition.from_state} → {transition.to_state} "
        f"[read: {read_str}, pop: {pop_str}, push: {push_str}]"
    )
    new_config.add_history(history_entry)

    return new_config


def stepwise_run(
        automaton: Automaton,
        input_string: str,
        mode: str = "step",
        max_steps: Optional[int] = None,
        max_configs: int = DEFAULT_MAX_CONFIGS
) -> Iterator[list[PDAConfig]]:
    """Executa o autômato passo-a-passo, mantendo frontier de configurações.

    Em cada iteração, retorna snapshots de todas as configurações ativas
    para renderização. Suporta exploração completa do espaço não-determinístico.

    Args:
        automaton: Autômato a simular
        input_string: String de entrada
        mode: "step" (manual) ou "auto" (automático)
        max_steps: Limite de passos (None = usar default)
        max_configs: Limite de configurações simultâneas na frontier

    Yields:
        Lista de configurações ativas em cada passo

    Raises:
        RuntimeError: Se o limite de passos ou configurações for excedido
    """
    if max_steps is None:
        max_steps = DEFAULT_MAX_STEPS

    # Criar configuração inicial
    initial_stack = Stack()
    # Nota: Muitos PDAs assumem um símbolo inicial na pilha (ex: Z0)
    # mas isso deve ser configurado no loader/parser do YAML

    initial_config = PDAConfig(
        state=automaton.initial_state,
        remaining_input=list(input_string),
        stack=initial_stack,
        history=["Configuração inicial"]
    )

    # Frontier de configurações ativas
    frontier = [initial_config]
    step_count = 0

    # Yield configuração inicial
    yield frontier.copy()

    # Executar até frontier vazia ou atingir limite
    while frontier:
        step_count += 1

        if step_count > max_steps:
            raise RuntimeError(
                f"Limite de passos excedido ({max_steps}). "
                f"Possível loop infinito ou entrada muito complexa."
            )

        # Aplicar todas as transições possíveis a todas as configurações
        next_frontier = []
        for config in frontier:
            next_configs = simulate_step(config, automaton)
            next_frontier.extend(next_configs)

        # Verificar explosão do espaço de busca
        if len(next_frontier) > max_configs:
            # Aplicar poda: manter apenas as configurações mais promissoras
            next_frontier = _prune_configurations(
                next_frontier,
                automaton,
                max_configs
            )

        frontier = next_frontier

        # Se não há mais configurações, terminar
        if not frontier:
            break

        # Yield frontier atual
        yield frontier.copy()


def _prune_configurations(
        configs: list[PDAConfig],
        automaton: Automaton,
        max_configs: int
) -> list[PDAConfig]:
    """Aplica heurística para reduzir o número de configurações.

    Heurísticas aplicadas (em ordem de prioridade):
    1. Preferir configurações em estados finais
    2. Preferir configurações com menos entrada restante
    3. Preferir configurações com pilha menor

    Args:
        configs: Lista de configurações a podar
        automaton: Autômato (para verificar estados finais)
        max_configs: Número máximo de configurações a manter

    Returns:
        Lista podada de configurações
    """
    def score_config(config: PDAConfig) -> tuple:
        """Calcula score para ordenação (maior é melhor)."""
        in_final_state = 1 if config.state in automaton.final_states else 0
        input_consumed = -len(config.remaining_input)  # Menos é melhor
        stack_size = -len(config.stack)  # Menor é melhor
        return (in_final_state, input_consumed, stack_size)

    # Ordenar por score e pegar os melhores
    sorted_configs = sorted(configs, key=score_config, reverse=True)
    return sorted_configs[:max_configs]


def accepts(
        automaton: Automaton,
        input_string: str,
        max_steps: Optional[int] = None,
        acceptance_mode: str = "final_state"
) -> tuple[bool, Optional[list[str]]]:
    """Verifica se o autômato aceita a string de entrada.

    Executa a simulação completa e retorna se a string foi aceita,
    junto com o trace de uma execução aceita (se existir).

    Args:
        automaton: Autômato a verificar
        input_string: String de entrada
        max_steps: Limite de passos (None = usar default)
        acceptance_mode: "final_state" (aceita em estado final com entrada vazia)
                        ou "empty_stack" (aceita com pilha vazia)

    Returns:
        Tupla (aceito, trace) onde:
        - aceito: True se a string é aceita, False caso contrário
        - trace: Lista de descrições das transições do caminho aceito,
                 ou None se não foi aceita

    Raises:
        RuntimeError: Se o limite de passos for excedido
        ValueError: Se acceptance_mode for inválido
    """
    if acceptance_mode not in ("final_state", "empty_stack"):
        raise ValueError(
            f"acceptance_mode inválido: {acceptance_mode}. "
            f"Use 'final_state' ou 'empty_stack'."
        )

    if max_steps is None:
        max_steps = DEFAULT_MAX_STEPS

    # Criar configuração inicial
    initial_stack = Stack()
    initial_config = PDAConfig(
        state=automaton.initial_state,
        remaining_input=list(input_string),
        stack=initial_stack,
        history=["Início da execução"]
    )

    frontier = [initial_config]
    step_count = 0

    while frontier:
        step_count += 1

        if step_count > max_steps:
            raise RuntimeError(
                f"Limite de passos excedido ({max_steps}). "
                f"Possível loop infinito."
            )

        # Verificar se alguma configuração atual é aceita
        for config in frontier:
            if _is_accepting_configuration(config, automaton, acceptance_mode):
                return True, config.history

        # Expandir frontier
        next_frontier = []
        for config in frontier:
            next_configs = simulate_step(config, automaton)
            next_frontier.extend(next_configs)

        # Aplicar poda se necessário
        if len(next_frontier) > DEFAULT_MAX_CONFIGS:
            next_frontier = _prune_configurations(
                next_frontier,
                automaton,
                DEFAULT_MAX_CONFIGS
            )

        frontier = next_frontier

    # Não encontrou configuração aceita
    return False, None


def _is_accepting_configuration(
        config: PDAConfig,
        automaton: Automaton,
        acceptance_mode: str
) -> bool:
    """Verifica se uma configuração é aceita.

    Args:
        config: Configuração a verificar
        automaton: Autômato
        acceptance_mode: "final_state" ou "empty_stack"

    Returns:
        True se a configuração é aceita, False caso contrário
    """
    # Entrada deve estar completamente consumida
    if not config.is_input_empty():
        return False

    if acceptance_mode == "final_state":
        # Aceita se está em estado final
        return config.state in automaton.final_states
    else:  # empty_stack
        # Aceita se a pilha está vazia
        return config.stack.is_empty()