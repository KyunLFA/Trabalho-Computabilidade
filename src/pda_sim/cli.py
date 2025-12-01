import argparse
import json
from pathlib import Path
from .config.loader import load_automaton
from .core.simulator import stepwise_run, accepts
from .render.ascii_render import render_automaton_unicode
from .render.step_view import render_step_list
import yaml
import sys

def interactive_build():
    print("== Construtor interativo de autômato ==")
    automaton_type = input("Tipo (pda/dfa) [pda]: ").strip() or "pda"
    states = input("Estados (separados por vírgula, ex.: q0,q1,qf): ").strip().split(',')
    states = [s.strip() for s in states if s.strip()]
    input_alphabet = input("Alfabeto de entrada (ex.: a,b): ").strip().split(',')
    input_alphabet = [s.strip() for s in input_alphabet if s.strip()]
    stack_alphabet = []
    initial_stack_symbol = None
    if automaton_type == "pda":
        stack_alphabet = input("Alfabeto da pilha (ex.: Z0,A) [enter para vazio]: ").strip().split(',')
        stack_alphabet = [s.strip() for s in stack_alphabet if s.strip()]
        initial_stack_symbol = input("Símbolo inicial da pilha (ex.: Z0) [deixe vazio para não usar]: ").strip() or None
    initial_state = input("Estado inicial (ex.: q0): ").strip()
    final_states = input("Estados finais (separados por vírgula): ").strip().split(',')
    final_states = [s.strip() for s in final_states if s.strip()]

    transitions = []
    print("\nDigite transições (uma por linha) no formato:")
    print("from,to,read,pop,push")
    print("Use 'ε' para no-op, '?' para teste de vazio. Exemplos de push: AZ0 ou '' para ε.")
    print("Quando terminar, pressione Enter em linha vazia.")

    while True:
        line = input("> ").strip()
        if not line:
            break
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 5:
            print("Esperado 5 campos: from,to,read,pop,push")
            continue
        frm,to,read,pop,push = parts[:5]
        push_list = [] if push in ('','ε') else list(push)
        transitions.append({'from':frm,'to':to,'read':read or 'ε','pop':pop or 'ε','push':push_list})

    spec = {
        'automaton_type': automaton_type,
        'states': states,
        'input_alphabet': input_alphabet,
        'stack_alphabet': stack_alphabet,
        'initial_state': initial_state,
        'initial_stack_symbol': initial_stack_symbol,
        'final_states': final_states,
        'transitions': transitions
    }

    fname = input("Arquivo para salvar (yaml/json) [automaton.yaml]: ").strip() or "automaton.yaml"
    if fname.endswith('.json'):
        Path(fname).write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding='utf-8')
    else:
        Path(fname).write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True), encoding='utf-8')
    print(f"Salvo em {fname}")
    return fname

def _run_with_prompt(file_path):
    A = load_automaton(file_path)
    print("\nAutômato criado:")
    print(render_automaton_unicode(A))
    run_now = input("\nDeseja executar agora este autômato? (s/n) [n]: ").strip().lower() or 'n'
    if run_now != 's':
        return
    inp = input("Entrada para testar (ex.: aaabbb) [deixar vazio para cadeia vazia]: ")
    mode = input("Modo de simulação (step/auto/rand) [step]: ").strip() or "step"
    acceptance = input("Modo de aceitação (final_state/empty_stack) [final_state]: ").strip() or "final_state"

    # run
    if mode == 'step':
        for frontier in stepwise_run(A, inp, mode='step'):
            print(render_step_list(frontier))
            input("Pressione Enter para o próximo passo...")
        accepted, trace = accepts(A, inp, acceptance_mode=acceptance)
        print("ACEITO" if accepted else "REJEITADO")
        if trace:
            print("Trace:")
            for l in trace:
                print("  ", l)
    else:
        for frontier in stepwise_run(A, inp, mode=mode):
            print(render_step_list(frontier))
        accepted, trace = accepts(A, inp, acceptance_mode=acceptance)
        print("ACEITO" if accepted else "REJEITADO")
        if trace:
            print("Trace:")
            for l in trace:
                print("  ", l)

def main():
    parser = argparse.ArgumentParser(description="Simulador PDA/AFD (Português BR)")
    subparsers = parser.add_subparsers(dest='cmd', required=True)
    debug = False

    runp = subparsers.add_parser('run', help='Executar autômato a partir de arquivo')
    runp.add_argument('--file', required=True, help='Caminho do arquivo YAML/JSON/ASCII')
    runp.add_argument('--input', required=False, default="", help='Cadeia de entrada (ex.: aaabbb)')
    runp.add_argument('--mode', choices=['step','auto','rand'], default='step', help='Modo de simulação')
    runp.add_argument('--acceptance', choices=['final_state','empty_stack'], default='final_state', help='Modo de aceitação')

    drawp = subparsers.add_parser('draw', help='Desenhar/mostrar o autômato em texto')
    drawp.add_argument('--file', required=True, help='Caminho do arquivo YAML/JSON/ASCII')

    valp = subparsers.add_parser('validate', help='Validar o arquivo do autômato')
    valp.add_argument('--file', required=True, help='Caminho do arquivo YAML/JSON/ASCII')

    intp = subparsers.add_parser('interactive', help='Construir autômato interativamente')
    intp.add_argument('--run', action='store_true', help='Executar o autômato imediatamente após criar')

    args = parser.parse_args()

    if args.cmd == 'interactive':
        fname = interactive_build()
        if args.run:
            _run_with_prompt(fname)
        else:
            print("\nAutômato salvo. Para executar rode: python -m pda_sim.cli run --file", fname)
        return

    if args.cmd == 'draw':
        A = load_automaton(args.file)
        print(render_automaton_unicode(A))
        return

    if args.cmd == 'validate':
        A = load_automaton(args.file)
        print("OK")
        return

    if args.cmd == 'run':
        A = load_automaton(args.file)
        print(render_automaton_unicode(A))
        inp = args.input or ""
        if args.mode == 'step':
            for frontier in stepwise_run(A, inp, mode='step'):
                print(render_step_list(frontier))
                input("Pressione Enter para continuar...")
            accepted, trace = accepts(A, inp, acceptance_mode=args.acceptance)
            print("ACEITO" if accepted else "REJEITADO")
            if trace:
                print("Trace:")
                for l in trace:
                    print("  ", l)
            return
        else:
            for frontier in stepwise_run(A, inp, mode=args.mode):
                print(render_step_list(frontier))
            accepted, trace = accepts(A, inp, acceptance_mode=args.acceptance)
            print("ACEITO" if accepted else "REJEITADO")
            if debug:
                print("Trace:")
                for l in trace:
                    print("  ", l)
            return

if __name__ == '__main__':
    main()
