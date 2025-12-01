import json
from pathlib import Path
from typing import Dict, Any
import yaml
from pda_sim.tools.validators import validate_spec, ValidationError 

class Loader:
    @staticmethod
    def from_file(path: str) -> Dict[str, Any]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

        suffix = p.suffix.lower()

        if suffix in ['.yaml', '.yml']:
            try:
                spec = yaml.safe_load(p.read_text(encoding='utf-8'))
            except yaml.YAMLError as e:
                raise ValueError(f"Erro ao interpretar YAML no arquivo {path}: {e}")
        elif suffix == '.json':
            try:
                spec = json.loads(p.read_text(encoding='utf-8'))
            except json.JSONDecodeError as e:
                raise ValueError(f"Erro ao interpretar JSON no arquivo {path}: {e}")
        else:
            spec = Loader._parse_mini_ascii(p.read_text(encoding='utf-8'))

        try:
            validate_spec(spec)
        except ValidationError as e:
            raise ValueError(f"Validação falhou para {path}: {e}") from e

        return spec

    @staticmethod
    def _parse_mini_ascii(text: str) -> Dict[str, Any]:
        spec = {
            'alphabet': [],
            'stack_alphabet': [],
            'states': [],
            'initial': None,
            'finals': [],
            'transitions': []
        }

        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith('#')]
        mode = None

        for i, ln in enumerate(lines, start=1):
            if ':' in ln and '->' not in ln:
                key, rest = [s.strip() for s in ln.split(':', 1)]
                if key.lower() == 'alphabet':
                    spec['alphabet'] = rest.split()
                elif key.lower() in ('stack_alphabet', 'stackalphabet'):
                    spec['stack_alphabet'] = rest.split()
                elif key.lower() == 'states':
                    spec['states'] = rest.split()
                elif key.lower() == 'initial':
                    spec['initial'] = rest
                elif key.lower() in ('finals', 'final'):
                    spec['finals'] = rest.split()
                elif key.lower() == 'transitions':
                    mode = 'transitions'
                continue

            if '->' in ln:
                left, right = [p.strip() for p in ln.split('->', 1)]
                parts = left.split()
                if len(parts) < 3:
                    raise ValueError(f"Linha {i}: transição mal formada: '{ln}'")

                estado, simbolo, topo = parts[0], parts[1], parts[2]
                right_parts = right.split()
                novo_estado = right_parts[0]
                push = right_parts[1] if len(right_parts) > 1 else ''

                spec['transitions'].append({
                    'from': estado,
                    'read': None if simbolo in ('eps', 'ε', '') else simbolo,
                    'pop': topo,
                    'to': novo_estado,
                    'push': '' if push in ('', '\"\"') else push
                })

        return spec
