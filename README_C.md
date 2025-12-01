# PDA Simulator – Interface de Linha de Comando (CLI)

Este módulo fornece a interface de terminal do simulador de Autômatos com Pilha (PDA).
Ele organiza a execução do programa, conecta os componentes internos e oferece três
operações principais ao usuário final.

## 📌 Funcionalidades do CLI

### `draw`
Desenha o autômato em ASCII com base em um arquivo YAML.
``bashs
python -m pda_sim.cli draw --file examples/exemplo1.yaml

Executa o autômato sobre uma entrada fornecida.

python -m pda_sim.cli run --file examples/exemplo1.yaml --input "abba"


Verifica se o arquivo YAML respeita a estrutura esperada.
python -m pda_sim.cli validate --file automato.yaml


