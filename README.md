# Algoritmo Raft em Sistemas Distribuídos

## Descrição do Projeto

Este projeto implementa um algoritmo de eleição para sistemas distribuídos, inspirado no modelo de consenso Raft. O objetivo principal é garantir que um único líder seja eleito em uma rede de nós, mesmo em cenários de falha. O código simula o comportamento de nós que alternam entre três estados: **follower**, **candidate** e **leader**, além de gerenciar a comunicação entre eles por meio de uma rede simulada.

Funcionalidades principais:
- Eleição de líder com base em votos.
- Comunicação entre nós via mensagens simuladas.
- Detecção de falhas e recuperação de nós.
- Monitoramento do status da rede.

## Configuração do Ambiente

### Requisitos

- **Python 3.7+**
- Biblioteca padrão do Python (`threading`, `random`, `time`, `queue`)

### Passos para Configuração

1. Clone o repositório:
   ```bash
   git clone https://github.com/jvrocha91/Raft_consensus_algorithm.git
   
2. Navegue até o diretório do projeto:
   cd sistema-distribuido
   
3.Execute o código
   python main.py

## Execução do Código
Ao executar o código, ele simula uma rede de cinco nós por 60 segundos. Durante esse período:

Os nós alternam entre estados com base em mensagens e eventos simulados.
O monitor de status exibe o estado atual de cada nó a cada 10 segundos.
Para finalizar a execução, o programa interrompe todos os nós após 60 segundos de simulação.

## Explicação do Algoritmo
O algoritmo implementa os seguintes comportamentos para cada estado:

##Estados dos Nós
Follower:
Aguarda mensagens de heartbeat do líder.
Inicia uma eleição ao detectar ausência de heartbeat (timeout).

Candidate:
Incrementa o termo atual e solicita votos dos outros nós.
Torna-se líder se obter a maioria dos votos.
Retorna ao estado de follower caso não ganhe a eleição.

Leader:
Envia mensagens de heartbeat para manter sua liderança.
Garante que todos os seguidores reconheçam seu estado de líder.

##Comunicação entre Nós
A classe Network simula a rede de comunicação. Cada nó possui uma fila para receber mensagens e métodos para enviar e difundir mensagens para os outros nós.

##Simulação de Falhas e Respostas do Sistema
##Falhas Simuladas

##Falha aleatória:
Um nó pode falhar aleatoriamente com 10% de chance por ciclo.
Um nó inativo é removido como líder e não participa da comunicação.

##Timeout de heartbeat:
Se um follower não receber um heartbeat dentro do intervalo definido, ele inicia uma eleição.

##Recuperação
Os nós inativos se recuperam após um tempo fixo de 5 segundos.
Durante a recuperação, o nó reseta seu estado para follower.

##Resposta do Sistema
Se o líder falhar, uma nova eleição é iniciada automaticamente.
A rede garante que, após falhas e recuperações, apenas um líder válido esteja ativo.

##Monitoramento e Logs
O monitor de status exibe o estado de todos os nós a cada 10 segundos.
Mensagens de log detalham eventos como mudanças de estado, falhas e recuperações.

##Possíveis Melhorias
Implementação de replicação de logs para aumentar a confiabilidade.
Otimização dos tempos de timeout para cenários maiores.
Suporte a testes de carga e integração.

Este projeto é uma simulação educacional e pode ser adaptado para cenários mais complexos de sistemas distribuídos. Caso tenha dúvidas, contribuições ou sugestões, abra uma issue no repositório.
