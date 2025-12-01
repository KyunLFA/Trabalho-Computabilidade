# src/pda_sim/core/simulator.py
from typing import List, Optional, Tuple, Iterator, Dict
from .config import PDAConfig
from .stack import Stack
from .automaton import Automaton, Transition
import random
import copy

DEFAULT_MAX_STEPS = 5000
DEFAULT_MAX_CONFIGS = 2000
# quantas vezes a mesma configuração (assinatura) pode reaparecer antes de ser bloqueada
DEFAULT_MAX_VISITS_PER_SIGNATURE = 50

def _signature_of_config(cfg: PDAConfig) -> Tuple[str, Tuple[str,...], Tuple[str,...]]:
    return (cfg.state, tuple(cfg.remaining_input), tuple(cfg.stack.items()))

def _is_transition_applicable(transition: Transition, cfg: PDAConfig, automaton: Automaton) -> bool:
    """
    Checa se a transição é aplicável à configuração corrente (apenas leitura de guardas,
    sem efetuar pop/push). Esta função considera corretamente 'ε' e '?'.
    """
    current = cfg.get_current_input_symbol()  # None if empty
    if transition.read == 'ε':
        read_ok = True
    elif transition.read == '?':
        read_ok = cfg.is_input_empty()
    else:
        read_ok = (current == transition.read)

    if not read_ok:
        return False

    try:
        top = cfg.stack.peek()
    except Exception:
        top = None

    if transition.pop == 'ε':
        pop_ok = True
    elif transition.pop == '?':
        if cfg.stack.is_empty():
            pop_ok = True
        elif automaton.initial_stack_symbol is None:
            pop_ok = False
        else:
            pop_ok = (len(cfg.stack) == 1 and cfg.stack.peek() == automaton.initial_stack_symbol)
    else:
        pop_ok = (top == transition.pop)

    return pop_ok

def _apply_transition(cfg: PDAConfig, transition: Transition) -> PDAConfig:
    """
    Aplica a transição e retorna uma nova configuração (cópia).
    Trata corretamente semantica read='ε'/'?' e pop='ε'/'?'.
    """
    new_cfg = cfg.copy()
    new_cfg.state = transition.to_state

    if transition.read not in ('ε', '?'):
        if new_cfg.remaining_input:
            new_cfg.consume_input()

    if transition.pop not in ('ε', '?'):
        try:
            new_cfg.stack.pop()
        except IndexError:
            pass

    if transition.push:
        new_cfg.stack.push(tuple(transition.push))

    push_str = "".join(transition.push) if transition.push else "ε"
    new_cfg.add_history(f"{transition.from_state}->{transition.to_state} [read:{transition.read} pop:{transition.pop} push:{push_str}]")
    return new_cfg

def _natural_sort_key_state(s: str):
    # Ordenação natural: q0, q1, q10 ...
    m = re.match(r'([^\d]*)(\d+)$', s)
    if m:
        return (m.group(1), int(m.group(2)))
    return (s, 0)

def _is_accepting_cfg(cfg: PDAConfig, automaton: Automaton, acceptance_mode: str) -> bool:
    """
    Critério de aceitação:
      - 'final_state' : aceita se o estado atual for final (IGNORA remaining_input).
      - 'empty_stack'  : aceita somente se remaining_input estiver vazia e pilha vazia (ou apenas símbolo inicial).
    """
    if acceptance_mode == "final_state":
        return cfg.state in automaton.final_states
    elif acceptance_mode == "empty_stack":
        # requer fita vazia e pilha vazia (ou apenas symbol inicial)
        if not cfg.is_input_empty():
            return False
        if cfg.stack.is_empty():
            return True
        if automaton.initial_stack_symbol is not None and len(cfg.stack) == 1 and cfg.stack.peek() == automaton.initial_stack_symbol:
            return True
        return False
    else:
        raise ValueError("acceptance_mode must be 'final_state' or 'empty_stack'")

def simulate_step(cfg: PDAConfig, automaton: Automaton) -> List[PDAConfig]:
    """
    Retorna todas as configurações resultantes de aplicar *uma* transição
    a partir de cfg, com a restrição de que só são permitidas transições
    que vão para o mesmo estado (self-loop) ou para um estado 'à frente'
    na ordem natural dos estados.
    """
    # cria ordering map (estado -> índice) usando ordenação natural
    try:
        ordered_states = sorted(list(automaton.states), key=_natural_sort_key_state)
    except Exception:
        ordered_states = sorted(list(automaton.states))
    order_map = {s: i for i, s in enumerate(ordered_states)}

    # transições do estado (embaralhadas para evitar vieses)
    trans_list = list(automaton.get_transitions_from(cfg.state))
    random.shuffle(trans_list)

    # determina índice do estado atual; se não existir na lista, assume 0
    cur_idx = order_map.get(cfg.state, 0)

    nexts: List[PDAConfig] = []
    for t in trans_list:
        # Se o destino não estiver no mapa, permitir (fallback), mas evitar 'voltar' se possível
        to_idx = order_map.get(t.to_state, None)
        # Regras de aceitação da transição conforme semântica (ε/?/símbolo) e top da pilha
        # Primeiro, aplique checagens de guardas (mesma lógica anterior)
        if not _is_transition_applicable(t, cfg, automaton):
            continue

        # Agora aplique a restrição de "forward-only":
        # permitimos se: to_idx is None (desconhecido), or to_idx >= cur_idx (mesmo ou à frente)
        if to_idx is not None and to_idx < cur_idx:
            continue

        # Se passou no teste, aplique a transição
        nexts.append(_apply_transition(cfg, t))

    return nexts

def _prune(configs: List[PDAConfig], automaton: Automaton, max_configs:int) -> List[PDAConfig]:
    """
    Prune heurístico: prioriza configurações que estão mais perto de aceitar:
      1) estado final
      2) menor input restante
      3) menor tamanho de pilha (preferir desempilhar)
    Limita a `max_configs`.
    """
    def score(c:PDAConfig):
        in_final = 1 if c.state in automaton.final_states else 0
        rem = -len(c.remaining_input)
        stack_sz = -len(c.stack)
        return (in_final, rem, stack_sz)
    sortedc = sorted(configs, key=score, reverse=True)
    return sortedc[:max_configs]

def stepwise_run(automaton: Automaton, input_string: str, mode: str = "step",
                 max_steps: Optional[int]=None, max_configs:int=DEFAULT_MAX_CONFIGS,
                 max_visits_per_signature:int=DEFAULT_MAX_VISITS_PER_SIGNATURE,
                 acceptance_mode: str = "final_state") -> Iterator[List[PDAConfig]]:
    """
    Iterador que gera a frontier (lista de configurações) a cada passo.
    Para 'final_state' agora aceitamos imediatamente se ANY configuração estiver em estado final,
    independentemente de ainda haver fita restante.
    """
    if max_steps is None:
        max_steps = DEFAULT_MAX_STEPS

    # inicializa pilha
    initial_stack = Stack()
    if automaton.initial_stack_symbol:
        initial_stack.push((automaton.initial_stack_symbol,))

    initial_cfg = PDAConfig(state=automaton.initial_state, remaining_input=list(input_string), stack=initial_stack, history=["start"])
    frontier = [initial_cfg]

    # visit-counts para assinaturas
    visit_counts: Dict[Tuple[str,Tuple[str,...],Tuple[str,...]], int] = {}
    visit_counts[_signature_of_config(initial_cfg)] = 1

    # se a configuração inicial já é aceitante, yield e pare
    if any(_is_accepting_cfg(c, automaton, acceptance_mode) for c in frontier):
        yield frontier.copy()
        return

    step = 0
    yield frontier.copy()

    while frontier:
        step += 1
        if step > max_steps:
            raise RuntimeError("max steps exceeded")

        if mode == "rand":
            # random-walk: escolha aleatória de configuração e de transição aplicável
            cfg = random.choice(frontier)
            nexts = simulate_step(cfg, automaton)
            if not nexts:
                # dead-end -> remove essa config da frontier
                frontier = [c for c in frontier if c is not cfg]
                # checar aceitação
                if any(_is_accepting_cfg(c, automaton, acceptance_mode) for c in frontier):
                    yield frontier.copy()
                    return
                yield frontier.copy()
                continue
            chosen = random.choice(nexts)
            sig = _signature_of_config(chosen)
            cnt = visit_counts.get(sig, 0)
            if cnt >= max_visits_per_signature:
                frontier = [c for c in frontier if c is not cfg]
                if any(_is_accepting_cfg(c, automaton, acceptance_mode) for c in frontier):
                    yield frontier.copy()
                    return
                yield frontier.copy()
                continue
            visit_counts[sig] = cnt + 1
            frontier = [chosen]
            # se a nova configuração for aceitante, yield e pare
            if any(_is_accepting_cfg(c, automaton, acceptance_mode) for c in frontier):
                yield frontier.copy()
                return
            yield frontier.copy()
            continue

        # modos 'auto' e 'step' (expansão em largura)
        next_frontier: List[PDAConfig] = []
        for cfg in frontier:
            nexts = simulate_step(cfg, automaton)
            for ncfg in nexts:
                sig = _signature_of_config(ncfg)
                cnt = visit_counts.get(sig, 0)
                if cnt >= max_visits_per_signature:
                    continue
                visit_counts[sig] = cnt + 1
                next_frontier.append(ncfg)

        # prune se estourou configs
        if len(next_frontier) > max_configs:
            next_frontier = _prune(next_frontier, automaton, max_configs)

        # se qualquer configuração de next_frontier for aceitante -> yield e pare
        if any(_is_accepting_cfg(c, automaton, acceptance_mode) for c in next_frontier):
            frontier = next_frontier
            yield frontier.copy()
            return

        frontier = next_frontier
        if frontier:
            yield frontier.copy()


def accepts(automaton: Automaton, input_string: str, max_steps: Optional[int]=None,
            acceptance_mode: str="final_state", max_visits_per_signature:int=DEFAULT_MAX_VISITS_PER_SIGNATURE) -> Tuple[bool, Optional[List[str]]]:
    """
    Verifica aceitação por BFS (explora até encontrar aceitação ou exaurir).
    'final_state' aceita assim que qualquer configuração estiver em estado final (independente da fita).
    """
    if acceptance_mode not in ("final_state","empty_stack"):
        raise ValueError("acceptance_mode must be 'final_state' or 'empty_stack'")

    if max_steps is None:
        max_steps = DEFAULT_MAX_STEPS

    initial_stack = Stack()
    if automaton.initial_stack_symbol:
        initial_stack.push((automaton.initial_stack_symbol,))

    initial_cfg = PDAConfig(state=automaton.initial_state, remaining_input=list(input_string), stack=initial_stack, history=["start"])
    frontier = [initial_cfg]
    visit_counts: Dict[Tuple[str,Tuple[str,...],Tuple[str,...]], int] = { _signature_of_config(initial_cfg): 1 }

    step = 0
    while frontier:
        step += 1
        if step > max_steps:
            raise RuntimeError("max steps exceeded")

        for cfg in frontier:
            if _is_accepting_cfg(cfg, automaton, acceptance_mode):
                return True, cfg.history

        next_frontier=[]
        for cfg in frontier:
            next_frontier.extend(simulate_step(cfg, automaton))

        filtered = []
        for ncfg in next_frontier:
            sig = _signature_of_config(ncfg)
            cnt = visit_counts.get(sig, 0)
            if cnt >= max_visits_per_signature:
                continue
            visit_counts[sig] = cnt + 1
            filtered.append(ncfg)
        frontier = filtered

    return False, None
