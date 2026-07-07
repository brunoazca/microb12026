# Testador de Componentes Complexos

## 📖 Sobre o Projeto

O Testador de Componentes Complexos é um sistema desenvolvido para identificar automaticamente componentes eletrônicos utilizando um Arduino MEGA e um software escrito em Python.

O usuário conecta um componente ao equipamento de teste e inicia o processo pela interface gráfica. O software executa uma sequência de testes utilizando diferentes formas de comunicação eletrônica e, ao final, identifica qual componente está conectado.

O principal benefício de nossa solução é a otimização de todo o processo é automatizado, reduzindo erros humanos e tornando a identificação muito mais rápida e confiável.

# 🧠 Como o sistema funciona?

O projeto é dividido em duas partes:

- Arduino: realiza a comunicação direta com o componente eletrônico e executa os testes.

- Aplicação em Python: controla os testes, recebe os resultados enviados pelo Arduino e apresenta as informações ao usuário através de uma interface gráfica desenvolvida com Tkinter.

```
Componente
     │
     ▼
 Arduino ───── Comunicação Serial ─────► Aplicação Python
     │                                      │
     └──────── Executa os testes ◄──────────┘
                       │
                       ▼
             Identificação do componente
```

# 💻 Interface gráfica

A aplicação possui uma interface desenvolvida com Tkinter, permitindo que o usuário execute todos os testes sem precisar utilizar o terminal ou conhecer programação.

A interface é responsável por:

- iniciar os testes;
- acompanhar o progresso;
- exibir mensagens de erro;
- mostrar o componente identificado;
- facilitar a operação do equipamento.

# 🔌 O que é comunicação serial?

Para que o computador consiga conversar com o Arduino, é utilizada uma comunicação serial.

Podemos imaginar essa comunicação como uma conversa entre duas pessoas:

- o computador envia uma mensagem;
- o Arduino recebe essa mensagem;
- o Arduino executa a tarefa solicitada;
- em seguida envia uma resposta de volta ao computador.

Essa troca de informações acontece através da porta USB utilizando a biblioteca PySerial.

# 📡 Protocolos de comunicação utilizados

Durante os testes, o Arduino utiliza diferentes protocolos para conversar com o componente conectado.

Cada componente pode responder de uma forma diferente, e essas respostas ajudam o sistema a identificar qual dispositivo está sendo testado.

## UART (Universal Asynchronous Receiver-Transmitter)

A UART é uma das formas mais simples de comunicação entre dispositivos eletrônicos.

Ela funciona enviando dados em sequência, um bit por vez, utilizando normalmente dois fios:

- transmissão (TX);
- recepção (RX).

É bastante utilizada em módulos GPS, Bluetooth, sensores e equipamentos industriais

## SPI (Serial Peripheral Interface)

O SPI é um protocolo de comunicação muito rápido.

Nele existe um dispositivo principal (o Arduino) que controla um ou mais dispositivos secundários.

A comunicação utiliza normalmente quatro sinais:

- MOSI (envio de dados);
- MISO (recebimento de dados);
- SCK (clock);
- CS/SS (seleção do dispositivo).

É comum em:

- memórias Flash;
- displays;
- conversores A/D;
- sensores de alta velocidade.

## I²C (Inter-Integrated Circuit)

O I²C permite que vários dispositivos compartilhem o mesmo barramento de comunicação.

Ele utiliza apenas dois fios:

- SDA (dados);
- SCL (clock).

Cada dispositivo possui um endereço próprio, permitindo que o Arduino converse com vários componentes usando o mesmo conjunto de fios.

É muito utilizado em:

- sensores;
- relógios de tempo real (RTC);
- expansores de portas;
- memórias EEPROM.

# 👷 Maintainers
<table>
  <tr>
    <td align="center"><a href="https://www.linkedin.com/in/bruno-azambuja-carvalho/"><img src="https://media.licdn.com/dms/image/v2/D4D03AQHt5XskxdwHjA/profile-displayphoto-crop_800_800/B4DZiMM5gQHwAI-/0/1754698848898?e=1784764800&v=beta&t=SBDuhszs19jh4P5vdCfz1i-W1ZHMIxK1feSw_oZBl6E" width="100px;" alt="Bruno Carvalho"/><br /><sub><b>Bruno Carvalho</b></sub></a><br /></td>
    <td align="center"><a href="https://www.linkedin.com/in/eduardo-meireles-438660373/"><img src="https://media.licdn.com/dms/image/v2/D4D03AQEN00OC1ciCnQ/profile-displayphoto-crop_800_800/B4DZ34pqPDI4AI-/0/1777993166090?e=1784764800&v=beta&t=t_9R9UzvdQpYwlvDsDdeY6fTtC6VFbxvddVb9J7Mops" width="100px;" alt="Eduardo Meireles"/><br /><sub><b>Eduardo Meireles</b></sub></a><br /></td>
    <td align="center"><a href="https://www.linkedin.com/in/gabriel-castello-branco-87871a302/"><img src="https://media.licdn.com/dms/image/v2/D4E03AQGwxT-wpORqZw/profile-displayphoto-crop_800_800/B4EZhEOIAgGcAM-/0/1753491211781?e=1784764800&v=beta&t=Cb9hdUn18M28g8hfSmQF65qlXn5eE5hTukQoP2ZHJjc" width="100px;" alt="Gabriel Castello Branco"/><br /><sub><b>Gabriel Castello Branco</b></sub></a><br /></td>
  </tr>
</table>

# ⚖️ Licença

Este projeto é distribuído sob a licença MIT.
