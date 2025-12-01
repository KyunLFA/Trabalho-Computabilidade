# Trabalho Computabilidade
Trabalho para disciplina de Computabilidade da Unisc.

Organizado pelo WhatsApp e dividido em partes para cada integrante.

O trabalho contempla usar Python através de CLI para demonstrar o funcionamento de PDAs (PushDown Automata)
ou autômatos com pilha. Utilizando o app (Linux, Windows) é póssível visualizar PDAs de forma intuitiva informando os parâmetros
iniciais: o alfabeto de entrada, a lista de estados, estado inicial e estado(s) fina(is), alfabeto da pilha e
as transições entre os estados.

Funcionalidades do CLI

Desenhar
Desenha o autômato em ASCII com base em um arquivo YAML.
``bash
python -m pda_sim.cli draw --file examples/exemplo1.yaml
``bash

run
Executa o autômato sobre uma entrada fornecida.
``bash
python -m pda_sim.cli run --file examples/exemplo1.yaml --input "abba"
``bash

validate
Verifica se o arquivo YAML respeita a estrutura esperada.
``bash
python -m pda_sim.cli validate --file automato.yaml
``bash
