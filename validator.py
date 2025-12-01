from typing import Dict, Any

class ValidationError(Exception):
    pass


def _require(key: str, spec: Dict[str, Any]):
    if key not in spec or spec[key] in (None, [], ''):
        raise ValidationError(f"Campo obrigatório ausente ou vazio: {key}")


def validate_spec(spec: Dict[str, Any]) -> bool:
    _require('alphabet', spec)
    _require('stack_alphabet', spec)
    _require('states', spec)
    _require('initial', spec)

    alphabet = set(spec['alphabet'])
    stack_alpha = set(spec['stack_alphabet'])
    states = set(spec['states'])

    initial = spec['initial']
    if initial not in states:
        raise ValidationError(f"Estado inicial '{initial}' não pertence à lista de estados")

    finals = set(spec.get('finals', []))
    if not finals.issubset(states):
        extra = finals - states
        raise ValidationError(f"Estados finais inválidos: {extra}")

    transitions = spec.get('transitions', [])
    if not isinstance(transitions, list):
        raise ValidationError("'transitions' deve ser uma lista")

    for idx, t in enumerate(transitions, start=1):
        try:
            frm = t['from']
            to = t['to']
            pop = t['pop']
            push = t.get('push', '')
            read = t.get('read', None)
        except Exception:
            raise ValidationError(f"Transição {idx} tem formato inválido: {t}")

        if frm not in states:
            raise ValidationError(f"Transição {idx}: estado de origem '{frm}' inexistente")
        if to not in states:
            raise ValidationError(f"Transição {idx}: estado destino '{to}' inexistente")

        if pop not in stack_alpha and pop != 'Z':
            raise ValidationError(f"Transição {idx}: topo da pilha inválido '{pop}'")

        if push and any(ch not in stack_alpha for ch in push):
            raise ValidationError(f"Transição {idx}: símbolo(s) a empilhar inválido(s): '{push}'")

        if read not in (None, '') and read not in alphabet:
            raise ValidationError(f"Transição {idx}: símbolo de leitura inválido '{read}'")

    return True
