# PDA Simulator – Interface de Linha de Comando (CLI)

Este módulo fornece a interface de terminal do simulador de Autômatos com Pilha (PDA).
Ele organiza a execução do programa, conecta os componentes internos e oferece três
operações principais ao usuário final.

 Funcionalidades do CLI

Draw
Desenha o autômato em ASCII com base em um arquivo YAML.
``bashs
python -m pda_sim.cli draw --file examples/exemplo1.yaml

run
Executa o autômato sobre uma entrada fornecida.
python -m pda_sim.cli run --file examples/exemplo1.yaml --input "abba"

validate
Verifica se o arquivo YAML respeita a estrutura esperada.
python -m pda_sim.cli validate --file automato.yaml


Estrutura
pda-simulator/
 ├── src/
 │    └── pda_sim/
 │         ├── cli.py                  # CLI implementado pela Pessoa C
 │         ├── config/
 │         │     └── loader.py         # Loader (Pessoa B)
 │         ├── core/
 │         │     └── simulator.py      # Simulador (Pessoa D)
 │         └── render/
 │               ├── ascii_renderer.py # Renderer ASCII (Pessoa A)
 │               └── step_view.py
 ├── examples/
 │    └── example1.yaml
 └── README.md
