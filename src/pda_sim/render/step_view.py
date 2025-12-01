def render_config(config):
    stack_str = " ".join(config.stack.items()[::-1]) if config.stack.items() else "ε"
    inp = "".join(config.remaining_input) if config.remaining_input else "ε"

    return (
        f"Estado: {config.state}\n"
        f"Entrada restante: {inp}\n"
        f"Pilha (topo à direita): {stack_str}\n"
    )


def render_step_list(configs):
    out = ["============================================"]

    if len(configs) == 1:
        out.append(render_config(configs[0]))
    else:
        for i, cfg in enumerate(configs):
            out.append(f"--- Configuração {i+1} ---")
            out.append(render_config(cfg))

    out.append("============================================")
    return "\n".join(out)

