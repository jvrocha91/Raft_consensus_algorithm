import threading
import random
import time
import queue


class Node:
    def __init__(self, node_id, network):
        self.node_id = node_id
        self.network = network
        self.state = "follower"  # Estados possíveis: follower, candidate, leader
        self.term = 0
        self.voted_for = None
        self.vote_count = 0
        self.heartbeat_timeout = random.uniform(5, 10)  # Timeout aleatório para detectar ausência de heartbeat
        self.last_heartbeat = time.time()  # Momento do último heartbeat recebido
        self.running = True  # Indica se o nó está rodando
        self.active = True  # Indica se o nó está ativo ou falho

    def run(self):
        """
        Método principal que define o comportamento do nó.
        Ele alterna entre os estados de follower, candidate ou leader.
        """
        while self.running:
            # Simula falha se o nó não estiver ativo
            if not self.active:
                print(f"Nó {self.node_id} está inativo (falhou).")
                time.sleep(5)
                self.recover()
                continue

            # Simula chance de falha aleatória (10% de chance a cada ciclo)
            if random.randint(1, 10) == 1:
                self.fail()
                continue

            # Alterna o comportamento do nó com base em seu estado atual
            if self.state == "follower":
                self.follower()
            elif self.state == "candidate":
                self.candidate()
            elif self.state == "leader":
                self.leader()
            time.sleep(1)

    def fail(self):
        """
        Simula a falha de um nó.
        """
        self.active = False
        if self.state == "leader":
            self.network.remove_leader()  # Remove o líder da rede
        self.state = "follower"  # Nó retorna ao estado de follower
        self.vote_count = 0  # Reseta a contagem de votos
        print(f"Nó {self.node_id} falhou.")

    def recover(self):
        """
        Recupera o nó para o estado ativo.
        """
        self.active = True
        self.last_heartbeat = time.time()  # Reseta o tempo do último heartbeat
        print(f"Nó {self.node_id} se recuperou.")

    def follower(self):
        """
        Comportamento do estado follower. Aguarda mensagens de heartbeat ou inicia eleição se timeout ocorrer.
        """
        if time.time() - self.last_heartbeat > self.heartbeat_timeout:
            print(f"Nó {self.node_id} não recebeu heartbeat, tornando-se candidate.")
            if not self.network.leader_exists():
                self.state = "candidate"
                self.vote_count = 0  # Reseta votos antes de se tornar candidato
            return
        self.wait_for_messages(timeout=1)

    def candidate(self):
        """
        Comportamento do estado candidate. Solicita votos e verifica se obteve a maioria.
        """
        print(f"Nó {self.node_id} está concorrendo à liderança (termo {self.term}).")
        self.term += 1
        self.voted_for = self.node_id
        self.vote_count = 1  # Vota em si mesmo
        self.network.broadcast_message({
            "type": "RequestVote",
            "term": self.term,
            "candidate_id": self.node_id
        })

        # Espera votos ou timeout
        start_time = time.time()
        while time.time() - start_time < self.heartbeat_timeout:
            try:
                message = self.network.receive_message(self.node_id)
                self.handle_message(message)
                if self.state == "leader":  # Se eleito líder, termina o ciclo
                    return
            except queue.Empty:
                continue

        print(f"Nó {self.node_id} não ganhou a eleição, retornando ao estado follower.")
        self.state = "follower"

    def leader(self):
        """
        Comportamento do estado leader. Envia mensagens de heartbeat para seguidores.
        """
        print(f"Nó {self.node_id} é o leader.")
        self.network.set_leader(self.node_id)
        while self.state == "leader" and self.running and self.active:
            self.network.broadcast_message({
                "type": "Heartbeat",
                "term": self.term,
                "leader_id": self.node_id
            })
            time.sleep(2)

    def wait_for_messages(self, timeout):
        """
        Aguarda mensagens recebidas pelo nó.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                message = self.network.receive_message(self.node_id)
                self.handle_message(message)
            except queue.Empty:
                continue

    def handle_message(self, message):
        """
        Processa mensagens recebidas de outros nós.
        """
        if message["type"] == "RequestVote":
            self.handle_vote_request(message)
        elif message["type"] == "Vote":
            self.handle_vote(message)
        elif message["type"] == "Heartbeat":
            self.handle_heartbeat(message)

    def handle_vote_request(self, message):
        """
        Processa solicitações de voto de candidatos.
        """
        if message["term"] >= self.term and self.voted_for in (None, message["candidate_id"]):
            self.term = message["term"]
            self.voted_for = message["candidate_id"]
            self.network.send_message(message["candidate_id"], {
                "type": "Vote",
                "term": self.term,
                "voter_id": self.node_id
            })
            print(f"Nó {self.node_id} votou no Nó {message['candidate_id']}.")

    def handle_vote(self, message):
        """
        Processa votos recebidos durante uma eleição.
        """
        if message["term"] == self.term:
            self.vote_count += 1
            print(f"Nó {self.node_id} recebeu um voto (total: {self.vote_count}).")
            if self.vote_count > len(self.network.nodes) // 2:
                print(f"Nó {self.node_id} ganhou a eleição e agora é o leader.")
                self.state = "leader"

    def handle_heartbeat(self, message):
        """
        Processa mensagens de heartbeat do líder.
        """
        if message["term"] >= self.term:
            self.term = message["term"]
            self.state = "follower"
            self.last_heartbeat = time.time()
            print(f"Nó {self.node_id} recebeu um heartbeat do Nó {message['leader_id']}.")


class Network:
    """
    Classe que simula a rede de comunicação entre os nós.
    """
    def __init__(self):
        self.nodes = {}
        self.queues = {}
        self.current_leader = None

    def add_node(self, node):
        self.nodes[node.node_id] = node
        self.queues[node.node_id] = queue.Queue()

    def send_message(self, target_id, message):
        self.queues[target_id].put(message)

    def broadcast_message(self, message):
        for node_id in self.nodes:
            self.send_message(node_id, message)

    def receive_message(self, node_id):
        return self.queues[node_id].get(timeout=1)

    def set_leader(self, leader_id):
        self.current_leader = leader_id
        print(f"O leader agora é o Nó {leader_id}.")

    def remove_leader(self):
        print(f"O leader {self.current_leader} não está mais ativo.")
        self.current_leader = None

    def leader_exists(self):
        return self.current_leader is not None and self.nodes[self.current_leader].active


def monitor_status(nodes):
    """
    Monitor de status: imprime o estado de todos os nós a cada 10 segundos.
    """
    while True:
        states = [f"Nó {node.node_id}: {node.state}" for node in nodes]
        print("\n==========\nStatus atual:\n","\n".join(states))
        print("==========\n")
        time.sleep(10)


def simulate():
    """
    Simula a execução do sistema distribuído por 60 segundos.
    """
    network = Network()
    nodes = [Node(i, network) for i in range(1,6)]

    for node in nodes:
        network.add_node(node)

    threads = [threading.Thread(target=node.run) for node in nodes]

    # Adiciona o monitor de status
    monitor_thread = threading.Thread(target=monitor_status, args=(nodes,))
    monitor_thread.daemon = True
    monitor_thread.start()

    for thread in threads:
        thread.start()

    # Simulação por 60 segundos
    time.sleep(60)

    for node in nodes:
        node.running = False

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    simulate()
