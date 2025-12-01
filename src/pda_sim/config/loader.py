import json, re
from pathlib import Path
from typing import Dict, Any, List
from ..core.automaton import Automaton

try:
    import yaml
except Exception:
    yaml = None

class AutomatonLoadError(Exception):
    pass

def load_automaton(path: str) -> Automaton:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    suffix = p.suffix.lower()
    if suffix in ('.yaml', '.yml'):
        return load_from_yaml(path)
    if suffix == '.json':
        return load_from_json(path)
    if suffix in ('.txt', '.pda', '.ascii'):
        return load_from_ascii(path)
    raise AutomatonLoadError("Unsupported format")

def _build_from_dict(d: Dict[str,Any], source:str) -> Automaton:
    # default = pda se não informado
    automaton_type = d.get('automaton_type', 'pda')

    # campos em comum
    required_common = ['states','input_alphabet','initial_state','final_states','transitions']
    for k in required_common:
        if k not in d:
            raise AutomatonLoadError(f"missing {k} in {source}")

    # stack_alphabet é somente se PDA
    if automaton_type == 'pda' and 'stack_alphabet' not in d:
        raise AutomatonLoadError(f"missing stack_alphabet in {source} for PDA")

    states = set(d['states'])
    input_alpha = set(d['input_alphabet'])
    stack_alpha = set(d.get('stack_alphabet', []))
    initial = d['initial_state']
    finals = set(d['final_states'])
    initial_stack_sym = d.get('initial_stack_symbol', None)

    if automaton_type == "pda":
        if initial_stack_sym is not None and initial_stack_sym not in stack_alpha:
            raise AutomatonLoadError("initial_stack_symbol not in stack_alphabet")

    A = Automaton(states=states, input_alphabet=input_alpha, stack_alphabet=stack_alpha,
                  initial_state=initial, final_states=finals, initial_stack_symbol=initial_stack_sym,
                  automaton_type=automaton_type)

    for idx, tr in enumerate(d['transitions'],1):
        for f in ('from','to','read','pop','push'):
            if f not in tr:
                raise AutomatonLoadError(f"transition {idx} missing {f}")
        frm = tr['from']; to = tr['to']; read = tr['read']; pop = tr['pop']; push = tr['push']
        # normalize push
        if isinstance(push, str):
            push = [] if push in ('ε','') else list(push)
        if not isinstance(push,(list,tuple)):
            raise AutomatonLoadError(f"push must be list at transition {idx}")

        # cheques básicos
        if read not in ('ε','?') and read not in input_alpha:
            if automaton_type == "pda":
                raise AutomatonLoadError(f"read '{read}' not in input alphabet at transition {idx}")
            else:
                raise AutomatonLoadError(f"read '{read}' not in input alphabet at transition {idx}")

        if pop not in ('ε','?') and automaton_type == "pda" and pop not in stack_alpha:
            raise AutomatonLoadError(f"pop '{pop}' not in stack alphabet at transition {idx}")

        if automaton_type == "pda":
            for s in push:
                if s not in stack_alpha:
                    raise AutomatonLoadError(f"push symbol '{s}' not in stack alphabet at transition {idx}")

        A.add_transition(from_state=frm, to_state=to, read=read, pop=pop, push=tuple(push))

    return A

def load_from_yaml(path: str) -> Automaton:
    if yaml is None:
        raise AutomatonLoadError("PyYAML not installed")
    raw = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    return _build_from_dict(raw, path)

def load_from_json(path: str) -> Automaton:
    raw = json.loads(Path(path).read_text(encoding='utf-8'))
    return _build_from_dict(raw, path)

def load_from_ascii(path: str) -> Automaton:
    text = Path(path).read_text(encoding='utf-8')
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith('#')]
    data = {
        'states': [], 'input_alphabet': [], 'stack_alphabet': [], 'initial_state': None,
        'initial_stack_symbol': None, 'final_states': [], 'transitions': []
    }
    trans_re = re.compile(r'^\s*(\w+)\s*->\s*(\w+)\s*\[([^\]]+)\]')
    for ln in lines:
        if ':' in ln and '->' not in ln:
            k,v = [s.strip() for s in ln.split(':',1)]
            K=k.lower()
            vals = [x.strip() for x in v.split(',') if x.strip()]
            if K in ('states','state','st'):
                data['states']=vals
            elif K in ('input','input_alphabet','alphabet'):
                data['input_alphabet']=vals
            elif K in ('stack','stack_alphabet'):
                data['stack_alphabet']=vals
            elif K in ('initial','initial_state'):
                data['initial_state']=vals[0] if vals else None
            elif K in ('initial_stack','initial_stack_symbol'):
                data['initial_stack_symbol']=vals[0] if vals else None
            elif K in ('final','finals','final_states'):
                data['final_states']=vals
            continue
        m = trans_re.match(ln)
        if m:
            frm,to,params = m.groups()
            pr = {'from':frm,'to':to,'read':'ε','pop':'ε','push':[]}
            for part in [p.strip() for p in params.split(',') if p.strip()]:
                if '=' not in part: continue
                k,v = [s.strip() for s in part.split('=',1)]
                if k=='read':
                    pr['read']=v
                elif k=='pop':
                    pr['pop']=v
                elif k=='push':
                    pr['push']=[] if v in ('ε','') else list(v)
            data['transitions'].append(pr)
            continue
        raise AutomatonLoadError(f"line not understood: {ln}")
    return _build_from_dict(data, path)
