from rich import print as rprint
from rich.table import Table

def render_config(cfg):
    stack_items = cfg.stack.items()
    stack_repr = "ε" if not stack_items else ",".join(stack_items)
    inp = "".join(cfg.remaining_input) if cfg.remaining_input else "ε"
    return f"Estado: {cfg.state}\nEntrada restante: {inp}\nPilha (fundo->topo): {stack_repr}\n"

def render_step_list(configs):
    out = ["="*50]
    if len(configs) == 1:
        out.append(render_config(configs[0]))
    else:
        for i,c in enumerate(configs,1):
            out.append(f"--- Config {i} ---")
            out.append(render_config(c))
    out.append("="*50)
    return "\n".join(out)
