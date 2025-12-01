import argparse

from .config.loader import load_automaton
from .core.simulator import stepwise_run
from .render.ascii_renderer import render_automaton
from .render.step_view import render_step_list

def main():
    parser = argparse.ArgumentParser(description="Simulador de PDA")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_cmd = subparsers.add_parser("run", help="Executa o autômato com uma entrada")
    run_cmd.add_argument("--file", required=True)
    run_cmd.add_argument("--input", required=True)
    run_cmd.add_argument("--mode", choices=["step", "auto"], default="step")

    draw_cmd = subparsers.add_parser("draw", help="Desenha o autômato em ASCII")
    draw_cmd.add_argument("--file", required=True)

    val_cmd = subparsers.add_parser("validate", help="Valida o arquivo de autômato")
    val_cmd.add_argument("--file", required=True)

    args = parser.parse_args()

    if args.command == "draw":
        automaton = load_automaton(args.file)
        print(render_automaton(automaton))
        return

    if args.command == "validate":
        automaton = load_automaton(args.file)
        print("Arquivo válido ✔")
        return

    if args.command == "run":
        automaton = load_automaton(args.file)
        if args.mode == "auto":
            for configs in stepwise_run(automaton, args.input, mode="auto"):
                print(render_step_list(configs))
            return

        for configs in stepwise_run(automaton, args.input, mode="step"):
            print(render_step_list(configs))
            input("Pressione ENTER para continuar...")
if __name__ == "__main__":
    main()
