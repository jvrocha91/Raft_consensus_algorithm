import threading
import random
import time
import queue


class Node:
    def __init__(self, node_id, network):
        self.node_id = node_id
        self.network = network
        self.state = "follower"  # states: follower, candidate, leader
        self.term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = -1
        self.vote_count = 0
        self.heartbeat_timeout = random.uniform(5, 10)  # Timeout aleatório
        self.last_heartbeat = time.time()
        self.running = True
        self.active = True  # Indica se o nó está ativo ou falho

    def run(self):
        while self.running:
            if not self.active:
                print(f"Node {self.node_id} is inactive (failed).")
                time.sleep(5)  # Tempo de falha
                self.recover()
                continue

            # Chance de falhar (1 em 10)
            if random.randint(1, 10) == 1:
                self.fail()
                continue

            if self.state == "follower":
                self.follower()
            elif self.state == "candidate":
                self.candidate()
            elif self.state == "leader":
                self.leader()
            time.sleep(1)

    def fail(self):
        """Simula a falha do nó."""
        self.active = False
        if self.state == "leader":
            self.network.remove_leader()
        self.state = "follower"
        self.vote_count = 0
        print(f"Node {self.node_id} has failed.")

    def recover(self):
        """Recupera o nó."""
        self.active = True
        self.last_heartbeat = time.time()
        print(f"Node {self.node_id} has recovered.")

    def follower(self):
        if time.time() - self.last_heartbeat > self.heartbeat_timeout:
            print(f"Node {self.node_id} did not receive heartbeat, becoming candidate.")
            if not self.network.leader_exists():
                self.state = "candidate"
                self.vote_count = 0
            return
        print(f"Node {self.node_id} is a follower.")
        self.wait_for_messages(timeout=1)

    def candidate(self):
        print(f"Node {self.node_id} is running for leader (term {self.term}).")
        self.term += 1
        self.voted_for = self.node_id
        self.vote_count = 1  # Voto no próprio nó
        self.network.broadcast_message({
            "type": "RequestVote",
            "term": self.term,
            "candidate_id": self.node_id
        })
        start_time = time.time()
        while time.time() - start_time < self.heartbeat_timeout:
            try:
                message = self.network.receive_message(self.node_id)
                self.handle_message(message)
                if self.state == "leader":
                    return
            except queue.Empty:
                continue

        # Timeout sem maioria, retorna a seguidor
        print(f"Node {self.node_id} did not win the election, returning to follower state.")
        self.state = "follower"

    def leader(self):
        print(f"Node {self.node_id} is the leader.")
        self.network.set_leader(self.node_id)
        while self.state == "leader" and self.running and self.active:
            self.network.broadcast_message({
                "type": "Heartbeat",
                "term": self.term,
                "leader_id": self.node_id
            })
            time.sleep(2)

    def wait_for_messages(self, timeout):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                message = self.network.receive_message(self.node_id)
                self.handle_message(message)
            except queue.Empty:
                continue

    def handle_message(self, message):
        if message["type"] == "RequestVote":
            self.handle_vote_request(message)
        elif message["type"] == "Vote":
            self.handle_vote(message)
        elif message["type"] == "Heartbeat":
            self.handle_heartbeat(message)

    def handle_vote_request(self, message):
        if message["term"] >= self.term and self.voted_for in (None, message["candidate_id"]):
            self.term = message["term"]
            self.voted_for = message["candidate_id"]
            self.network.send_message(message["candidate_id"], {
                "type": "Vote",
                "term": self.term,
                "voter_id": self.node_id
            })
            print(f"Node {self.node_id} voted for Node {message['candidate_id']}.")

    def handle_vote(self, message):
        if message["term"] == self.term:
            self.vote_count += 1
            print(f"Node {self.node_id} received a vote (total: {self.vote_count}).")
            if self.vote_count > len(self.network.nodes) // 2:
                print(f"Node {self.node_id} has won the election and is now the leader.")
                self.state = "leader"

    def handle_heartbeat(self, message):
        if message["term"] >= self.term:
            self.term = message["term"]
            self.state = "follower"
            self.last_heartbeat = time.time()
            print(f"Node {self.node_id} received a heartbeat from Node {message['leader_id']}.")


class Network:
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
        print(f"Leader is now Node {leader_id}.")

    def remove_leader(self):
        print(f"Leader Node {self.current_leader} is no longer active.")
        self.current_leader = None

    def leader_exists(self):
        return self.current_leader is not None and self.nodes[self.current_leader].active


def simulate():
    network = Network()
    nodes = [Node(i, network) for i in range(5)]

    for node in nodes:
        network.add_node(node)

    threads = [threading.Thread(target=node.run) for node in nodes]

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
