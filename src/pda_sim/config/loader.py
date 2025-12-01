"""Parsers e loaders para autômatos de pilha (PDA).

Suporta múltiplos formatos:
- YAML: formato estruturado e legível
- JSON: formato estruturado para APIs
- ASCII: mini-linguagem textual simples
- CSV: formato tabular para transições

Inclui validações completas de alfabetos, estados e transições.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set
from ..core.automaton import Automaton, Transition

try:
    import yaml
except ImportError:
    yaml = None


class AutomatonLoadError(Exception):
    """Exceção levantada quando há erro ao carregar autômato."""
    pass


def load_automaton(path: str) -> Automaton:
    """Carrega autômato detectando automaticamente o formato.

    Args:
        path: Caminho para o arquivo

    Returns:
        Autômato carregado e validado

    Raises:
        AutomatonLoadError: Se o arquivo não puder ser carregado
        FileNotFoundError: Se o arquivo não existir
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    suffix = file_path.suffix.lower()

    if suffix in ('.yaml', '.yml'):
        return load_from_yaml(path)
    elif suffix == '.json':
        return load_from_json(path)
    elif suffix in ('.txt', '.pda', '.ascii'):
        return load_from_ascii(path)
    elif suffix == '.csv':
        return load_from_csv(path)
    else:
        raise AutomatonLoadError(
            f"Formato não reconhecido: {suffix}. "
            f"Use .yaml, .json, .txt/.pda/.ascii, ou .csv"
        )


def load_from_yaml(path: str) -> Automaton:
    """Carrega autômato de arquivo YAML.

    Formato esperado:
    ```yaml
    states: [q0, q1, q2]
    input_alphabet: [a, b]
    stack_alphabet: [Z, X]
    initial_state: q0
    initial_stack: [Z]  # opcional
    final_states: [q2]
    transitions:
      - from: q0
        to: q1
        read: a
        pop: Z
        push: [X, Z]
      - from: q1
        to: q2
        read: ε
        pop: X
        push: []
    ```

    Args:
        path: Caminho para arquivo YAML

    Returns:
        Autômato carregado e validado

    Raises:
        AutomatonLoadError: Se houver erro no formato ou validação
    """
    if yaml is None:
        raise AutomatonLoadError(
            "PyYAML não está instalado. "
            "Instale com: pip install pyyaml"
        )

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise AutomatonLoadError(f"Erro ao parsear YAML: {e}")
    except Exception as e:
        raise AutomatonLoadError(f"Erro ao ler arquivo: {e}")

    return _build_automaton_from_dict(data, path)


def load_from_json(path: str) -> Automaton:
    """Carrega autômato de arquivo JSON.

    Formato esperado (similar ao YAML):
    ```json
    {
      "states": ["q0", "q1", "q2"],
      "input_alphabet": ["a", "b"],
      "stack_alphabet": ["Z", "X"],
      "initial_state": "q0",
      "initial_stack": ["Z"],
      "final_states": ["q2"],
      "transitions": [
        {
          "from": "q0",
          "to": "q1",
          "read": "a",
          "pop": "Z",
          "push": ["X", "Z"]
        }
      ]
    }
    ```

    Args:
        path: Caminho para arquivo JSON

    Returns:
        Autômato carregado e validado

    Raises:
        AutomatonLoadError: Se houver erro no formato ou validação
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise AutomatonLoadError(f"Erro ao parsear JSON: {e}")
    except Exception as e:
        raise AutomatonLoadError(f"Erro ao ler arquivo: {e}")

    return _build_automaton_from_dict(data, path)


def load_from_ascii(path: str) -> Automaton:
    """Carrega autômato de formato ASCII textual.

    Formato esperado:
    ```
    # Comentários começam com #
    STATES: q0, q1, q2
    INPUT: a, b
    STACK: Z, X
    INITIAL: q0
    INITIAL_STACK: Z  # opcional
    FINAL: q2

    # Transições (uma por linha)
    q0 -> q1 [read=a, pop=Z, push=XZ]
    q1 -> q2 [read=ε, pop=X, push=ε]
    q1 -> q1 [read=b, pop=X, push=XX]
    ```

    Args:
        path: Caminho para arquivo ASCII

    Returns:
        Autômato carregado e validado

    Raises:
        AutomatonLoadError: Se houver erro no formato ou validação
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        raise AutomatonLoadError(f"Erro ao ler arquivo: {e}")

    data = {
        'states': [],
        'input_alphabet': [],
        'stack_alphabet': [],
        'initial_state': None,
        'initial_stack': [],
        'final_states': [],
        'transitions': []
    }

    # Pattern para transições: q0 -> q1 [read=a, pop=Z, push=XZ]
    transition_pattern = re.compile(
        r'^\s*(\w+)\s*->\s*(\w+)\s*\[([^\]]+)\]'
    )

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Ignorar linhas vazias e comentários
        if not line or line.startswith('#'):
            continue

        # Tentar parsear como definição
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().upper()
            value = value.strip()

            # Parsear lista de valores separados por vírgula
            values = [v.strip() for v in value.split(',') if v.strip()]

            if key == 'STATES':
                data['states'] = values
            elif key == 'INPUT':
                data['input_alphabet'] = values
            elif key == 'STACK':
                data['stack_alphabet'] = values
            elif key == 'INITIAL':
                data['initial_state'] = values[0] if values else None
            elif key == 'INITIAL_STACK':
                data['initial_stack'] = values
            elif key == 'FINAL':
                data['final_states'] = values
            else:
                raise AutomatonLoadError(
                    f"Linha {line_num}: chave desconhecida '{key}'"
                )

        # Tentar parsear como transição
        elif '->' in line:
            match = transition_pattern.match(line)
            if not match:
                raise AutomatonLoadError(
                    f"Linha {line_num}: formato de transição inválido"
                )

            from_state, to_state, params = match.groups()

            # Parsear parâmetros
            trans_data = {
                'from': from_state,
                'to': to_state,
                'read': 'ε',
                'pop': 'ε',
                'push': []
            }

            for param in params.split(','):
                param = param.strip()
                if '=' not in param:
                    continue

                param_key, param_value = param.split('=', 1)
                param_key = param_key.strip()
                param_value = param_value.strip()

                if param_key == 'read':
                    trans_data['read'] = param_value if param_value != 'ε' else 'ε'
                elif param_key == 'pop':
                    trans_data['pop'] = param_value if param_value != 'ε' else 'ε'
                elif param_key == 'push':
                    if param_value == 'ε' or not param_value:
                        trans_data['push'] = []
                    else:
                        # push=XZ significa empilhar X depois Z
                        trans_data['push'] = list(param_value)

            data['transitions'].append(trans_data)
        else:
            raise AutomatonLoadError(
                f"Linha {line_num}: formato não reconhecido"
            )

    return _build_automaton_from_dict(data, path)


def load_from_csv(path: str) -> Automaton:
    """Carrega autômato de formato CSV tabular.

    Formato esperado:
    ```csv
    # Metadados (linhas começando com #META)
    #META,states,q0;q1;q2
    #META,input_alphabet,a;b
    #META,stack_alphabet,Z;X
    #META,initial_state,q0
    #META,initial_stack,Z
    #META,final_states,q2

    # Tabela de transições
    from,to,read,pop,push
    q0,q1,a,Z,XZ
    q1,q2,ε,X,ε
    q1,q1,b,X,XX
    ```

    Args:
        path: Caminho para arquivo CSV

    Returns:
        Autômato carregado e validado

    Raises:
        AutomatonLoadError: Se houver erro no formato ou validação
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        raise AutomatonLoadError(f"Erro ao ler arquivo: {e}")

    data = {
        'states': [],
        'input_alphabet': [],
        'stack_alphabet': [],
        'initial_state': None,
        'initial_stack': [],
        'final_states': [],
        'transitions': []
    }

    header_found = False

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Ignorar linhas vazias e comentários normais
        if not line or (line.startswith('#') and not line.startswith('#META')):
            continue

        # Parsear metadados
        if line.startswith('#META'):
            parts = line.split(',', 2)
            if len(parts) < 3:
                raise AutomatonLoadError(
                    f"Linha {line_num}: formato de metadado inválido"
                )

            _, key, value = parts
            key = key.strip()
            value = value.strip()

            # Valores separados por ponto-e-vírgula
            values = [v.strip() for v in value.split(';') if v.strip()]

            if key == 'states':
                data['states'] = values
            elif key == 'input_alphabet':
                data['input_alphabet'] = values
            elif key == 'stack_alphabet':
                data['stack_alphabet'] = values
            elif key == 'initial_state':
                data['initial_state'] = values[0] if values else None
            elif key == 'initial_stack':
                data['initial_stack'] = values
            elif key == 'final_states':
                data['final_states'] = values

            continue

        # Parsear header da tabela
        if not header_found:
            if line.lower().startswith('from'):
                header_found = True
            continue

        # Parsear transição
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 5:
            raise AutomatonLoadError(
                f"Linha {line_num}: transição incompleta (esperado 5 colunas)"
            )

        from_state, to_state, read, pop, push = parts[:5]

        trans_data = {
            'from': from_state,
            'to': to_state,
            'read': read if read != 'ε' else 'ε',
            'pop': pop if pop != 'ε' else 'ε',
            'push': list(push) if push and push != 'ε' else []
        }

        data['transitions'].append(trans_data)

    return _build_automaton_from_dict(data, path)


def _build_automaton_from_dict(data: Dict[str, Any], source_path: str) -> Automaton:
    """Constrói e valida autômato a partir de dicionário de dados.

    Args:
        data: Dicionário com dados do autômato
        source_path: Caminho do arquivo fonte (para mensagens de erro)

    Returns:
        Autômato validado

    Raises:
        AutomatonLoadError: Se houver erro de validação
    """
    # Validar campos obrigatórios
    required_fields = [
        'states', 'input_alphabet', 'stack_alphabet',
        'initial_state', 'final_states', 'transitions'
    ]

    for field in required_fields:
        if field not in data:
            raise AutomatonLoadError(f"Campo obrigatório ausente: {field}")

    # Converter para conjuntos
    states = set(data['states'])
    input_alphabet = set(data['input_alphabet'])
    stack_alphabet = set(data['stack_alphabet'])
    initial_state = data['initial_state']
    final_states = set(data['final_states'])

    # Validações básicas
    if not states:
        raise AutomatonLoadError("Conjunto de estados vazio")

    if not initial_state:
        raise AutomatonLoadError("Estado inicial não especificado")

    if initial_state not in states:
        raise AutomatonLoadError(
            f"Estado inicial '{initial_state}' não está no conjunto de estados"
        )

    if not final_states.issubset(states):
        unknown = final_states - states
        raise AutomatonLoadError(
            f"Estados finais desconhecidos: {unknown}"
        )

    # Criar autômato
    automaton = Automaton(
        states=states,
        input_alphabet=input_alphabet,
        stack_alphabet=stack_alphabet,
        initial_state=initial_state,
        final_states=final_states
    )

    # Processar pilha inicial (se especificada)
    if 'initial_stack' in data and data['initial_stack']:
        # Nota: a pilha inicial deve ser configurada no simulador
        # Aqui apenas validamos os símbolos
        for symbol in data['initial_stack']:
            if symbol not in stack_alphabet:
                raise AutomatonLoadError(
                    f"Símbolo de pilha inicial desconhecido: '{symbol}'"
                )

    # Processar transições
    for idx, trans_data in enumerate(data['transitions'], 1):
        try:
            _add_transition_from_dict(automaton, trans_data, idx)
        except AutomatonLoadError as e:
            raise AutomatonLoadError(f"Transição {idx}: {e}")

    return automaton


def _add_transition_from_dict(
        automaton: Automaton,
        trans_data: Dict[str, Any],
        index: int
) -> None:
    """Adiciona e valida uma transição ao autômato.

    Args:
        automaton: Autômato onde adicionar a transição
        trans_data: Dicionário com dados da transição
        index: Índice da transição (para mensagens de erro)

    Raises:
        AutomatonLoadError: Se a transição for inválida
    """
    # Validar campos obrigatórios
    required = ['from', 'to', 'read', 'pop', 'push']
    for field in required:
        if field not in trans_data:
            raise AutomatonLoadError(f"campo '{field}' ausente")

    from_state = trans_data['from']
    to_state = trans_data['to']
    read = trans_data['read']
    pop = trans_data['pop']
    push = trans_data['push']

    # Validar estados
    if from_state not in automaton.states:
        raise AutomatonLoadError(f"estado origem '{from_state}' desconhecido")

    if to_state not in automaton.states:
        raise AutomatonLoadError(f"estado destino '{to_state}' desconhecido")

    # Validar símbolo de leitura
    if read != 'ε' and read not in automaton.input_alphabet:
        raise AutomatonLoadError(
            f"símbolo de entrada '{read}' não está no alfabeto"
        )

    # Validar símbolo de pop
    if pop != 'ε' and pop not in automaton.stack_alphabet:
        raise AutomatonLoadError(
            f"símbolo de pilha '{pop}' não está no alfabeto de pilha"
        )

    # Validar e converter push para tupla
    if isinstance(push, str):
        push = list(push) if push and push != 'ε' else []

    if not isinstance(push, (list, tuple)):
        raise AutomatonLoadError(f"campo 'push' deve ser lista ou tupla")

    # Validar símbolos de push
    for symbol in push:
        if symbol not in automaton.stack_alphabet:
            raise AutomatonLoadError(
                f"símbolo de push '{symbol}' não está no alfabeto de pilha"
            )

    # Adicionar transição
    automaton.add_transition(
        from_state=from_state,
        to_state=to_state,
        read=read,
        pop=pop,
        push=tuple(push)
    )