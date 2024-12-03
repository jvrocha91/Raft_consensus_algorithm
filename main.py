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

    def run(self):
        while self.running:
            if self.state == "follower":
                self.follower()
            elif self.state == "candidate":
                self.candidate()
            elif self.state == "leader":
                self.leader()
            time.sleep(1)

    def follower(self):
        if time.time() - self.last_heartbeat > self.heartbeat_timeout:
            print(f"Node {self.node_id} did not receive heartbeat, becoming candidate.")
            self.state = "candidate"
            return
        print(f"Node {self.node_id} is a follower.")
        self.wait_for_messages(timeout=1)

    def candidate(self):
        print(f"Node {self.node_id} is running for leader (term {self.term}).")
        self.term += 1
        self.voted_for = self.node_id
        self.vote_count = 1
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

    def leader(self):
        print(f"Node {self.node_id} is the leader.")
        while self.state == "leader" and self.running:
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

def simulate():
    network = Network()
    nodes = [Node(i, network) for i in range(5)]

    for node in nodes:
        network.add_node(node)

    threads = [threading.Thread(target=node.run) for node in nodes]

    for thread in threads:
        thread.start()

    time.sleep(30)  # Run the simulation for 30 seconds

    for node in nodes:
        node.running = False

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    simulate()

