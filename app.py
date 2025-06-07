from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import hashlib
import json
import time
from datetime import datetime
import networkx as nx
import random
import heapq
from collections import defaultdict
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supply_chain_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Blockchain Implementation
class Transaction:
    def __init__(self, from_address, to_address, product_id, action, data, timestamp=None):
        self.from_address = from_address
        self.to_address = to_address
        self.product_id = product_id
        self.action = action  # 'create', 'transfer', 'quality_check', 'deliver'
        self.data = data
        self.timestamp = timestamp or datetime.now().isoformat()
        self.transaction_id = str(uuid.uuid4())

    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'product_id': self.product_id,
            'action': self.action,
            'data': self.data,
            'timestamp': self.timestamp
        }

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block mined: {self.hash}")

    def to_dict(self):
        return {
            'index': self.index,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 2
        self.pending_transactions = []
        self.mining_reward = 10

    def create_genesis_block(self):
        genesis_tx = Transaction("genesis", "genesis", "0", "create", {"message": "Genesis Block"})
        return Block(0, [genesis_tx], datetime.now().isoformat(), "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self):
        if not self.pending_transactions:
            return None
        
        block = Block(
            len(self.chain),
            self.pending_transactions[:10],  # Mine up to 10 transactions per block
            datetime.now().isoformat(),
            self.get_latest_block().hash
        )
        
        block.mine_block(self.difficulty)
        self.chain.append(block)
        
        # Remove mined transactions
        self.pending_transactions = self.pending_transactions[10:]
        
        socketio.emit('new_block', block.to_dict())
        return block

    def get_chain(self):
        return [block.to_dict() for block in self.chain]

# Supply Chain Network
class SupplyChainNetwork:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.companies = {}
        self.products = {}
        self.initialize_network()

    def initialize_network(self):
        # Create sample companies
        companies = [
            {"id": "farm1", "name": "Green Valley Farm", "type": "supplier", "location": (10, 10)},
            {"id": "factory1", "name": "Processing Plant A", "type": "manufacturer", "location": (30, 20)},
            {"id": "factory2", "name": "Packaging Corp", "type": "manufacturer", "location": (50, 25)},
            {"id": "dist1", "name": "Regional Distributor", "type": "distributor", "location": (70, 30)},
            {"id": "retail1", "name": "SuperMart", "type": "retailer", "location": (90, 40)},
            {"id": "retail2", "name": "Corner Store", "type": "retailer", "location": (85, 15)},
        ]
        
        for company in companies:
            self.add_company(company)
        
        # Create supply chain connections
        connections = [
            ("farm1", "factory1", {"cost": 5, "time": 2, "distance": 25}),
            ("factory1", "factory2", {"cost": 8, "time": 1, "distance": 20}),
            ("factory2", "dist1", {"cost": 12, "time": 3, "distance": 22}),
            ("dist1", "retail1", {"cost": 6, "time": 1, "distance": 25}),
            ("dist1", "retail2", {"cost": 4, "time": 1, "distance": 18}),
        ]
        
        for from_id, to_id, attrs in connections:
            self.graph.add_edge(from_id, to_id, **attrs)

    def add_company(self, company_data):
        company_id = company_data["id"]
        self.companies[company_id] = company_data
        self.graph.add_node(company_id, **company_data)

    def add_product(self, product_data):
        product_id = product_data["id"]
        self.products[product_id] = product_data

    def dijkstra_shortest_path(self, start, end, weight='cost'):
        try:
            path = nx.shortest_path(self.graph, start, end, weight=weight)
            cost = nx.shortest_path_length(self.graph, start, end, weight=weight)
            return path, cost
        except nx.NetworkXNoPath:
            return None, float('inf')

    def find_all_paths(self, start, end):
        try:
            paths = list(nx.all_simple_paths(self.graph, start, end))
            return paths
        except nx.NetworkXNoPath:
            return []

    def detect_supply_chain_vulnerabilities(self):
        vulnerabilities = []
        
        # Find single points of failure (articulation points)
        undirected = self.graph.to_undirected()
        articulation_points = list(nx.articulation_points(undirected))
        
        for point in articulation_points:
            vulnerabilities.append({
                "type": "single_point_of_failure",
                "node": point,
                "description": f"{self.companies[point]['name']} is a critical node"
            })
        
        return vulnerabilities

    def get_network_data(self):
        nodes = []
        edges = []
        
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": data["name"],
                "type": data["type"],
                "x": data["location"][0],
                "y": data["location"][1]
            })
        
        for from_node, to_node, data in self.graph.edges(data=True):
            edges.append({
                "from": from_node,
                "to": to_node,
                "cost": data["cost"],
                "time": data["time"],
                "distance": data["distance"]
            })
        
        return {"nodes": nodes, "edges": edges}

# Global instances
blockchain = Blockchain()
supply_network = SupplyChainNetwork()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/blockchain')
def get_blockchain():
    return jsonify(blockchain.get_chain())

@app.route('/api/network')
def get_network():
    return jsonify(supply_network.get_network_data())

@app.route('/api/create_product', methods=['POST'])
def create_product():
    data = request.json
    product_id = str(uuid.uuid4())
    
    product_data = {
        "id": product_id,
        "name": data["name"],
        "batch_number": data["batch_number"],
        "origin": data["origin"],
        "current_location": data["origin"],
        "quality_score": random.randint(85, 100),
        "created_at": datetime.now().isoformat()
    }
    
    supply_network.add_product(product_data)
    
    # Create blockchain transaction
    transaction = Transaction(
        "system",
        data["origin"],
        product_id,
        "create",
        product_data
    )
    
    blockchain.add_transaction(transaction)
    
    return jsonify({"success": True, "product_id": product_id, "product": product_data})

@app.route('/api/transfer_product', methods=['POST'])
def transfer_product():
    data = request.json
    product_id = data["product_id"]
    from_location = data["from"]
    to_location = data["to"]
    
    if product_id not in supply_network.products:
        return jsonify({"success": False, "error": "Product not found"})
    
    # Update product location
    supply_network.products[product_id]["current_location"] = to_location
    supply_network.products[product_id]["quality_score"] = max(80, 
        supply_network.products[product_id]["quality_score"] - random.randint(0, 5))
    
    # Create blockchain transaction
    transaction = Transaction(
        from_location,
        to_location,
        product_id,
        "transfer",
        {
            "quality_score": supply_network.products[product_id]["quality_score"],
            "transfer_time": datetime.now().isoformat()
        }
    )
    
    blockchain.add_transaction(transaction)
    
    return jsonify({"success": True, "transaction_id": transaction.transaction_id})

@app.route('/api/shortest_path')
def shortest_path():
    start = request.args.get('start')
    end = request.args.get('end')
    weight = request.args.get('weight', 'cost')
    
    path, cost = supply_network.dijkstra_shortest_path(start, end, weight)
    
    if path:
        return jsonify({
            "success": True,
            "path": path,
            "cost": cost,
            "path_details": [supply_network.companies[node]["name"] for node in path]
        })
    else:
        return jsonify({"success": False, "error": "No path found"})

@app.route('/api/trace_product/<product_id>')
def trace_product(product_id):
    if product_id not in supply_network.products:
        return jsonify({"success": False, "error": "Product not found"})
    
    # Find all transactions for this product
    product_transactions = []
    for block in blockchain.chain:
        for tx in block.transactions:
            if tx.product_id == product_id:
                product_transactions.append({
                    "block_index": block.index,
                    "transaction": tx.to_dict()
                })
    
    return jsonify({
        "success": True,
        "product": supply_network.products[product_id],
        "transactions": product_transactions
    })

@app.route('/api/mine')
def mine():
    block = blockchain.mine_pending_transactions()
    if block:
        return jsonify({"success": True, "block": block.to_dict()})
    else:
        return jsonify({"success": False, "message": "No transactions to mine"})

@app.route('/api/vulnerabilities')
def get_vulnerabilities():
    vulnerabilities = supply_network.detect_supply_chain_vulnerabilities()
    return jsonify(vulnerabilities)

@app.route('/api/products')
def get_products():
    return jsonify(list(supply_network.products.values()))

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('network_data', supply_network.get_network_data())

@socketio.on('request_mine')
def handle_mine_request():
    block = blockchain.mine_pending_transactions()
    if block:
        emit('mining_complete', block.to_dict(), broadcast=True)

if __name__ == '__main__':
    # Create some sample products
    sample_products = [
        {"name": "Organic Apples", "batch_number": "OA001", "origin": "farm1"},
        {"name": "Processed Apple Juice", "batch_number": "PAJ001", "origin": "factory1"},
        {"name": "Packaged Milk", "batch_number": "PM001", "origin": "farm1"}
    ]
    
    for product in sample_products:
        product_id = str(uuid.uuid4())
        product_data = {
            "id": product_id,
            "name": product["name"],
            "batch_number": product["batch_number"],
            "origin": product["origin"],
            "current_location": product["origin"],
            "quality_score": random.randint(85, 100),
            "created_at": datetime.now().isoformat()
        }
        supply_network.add_product(product_data)
        
        transaction = Transaction("system", product["origin"], product_id, "create", product_data)
        blockchain.add_transaction(transaction)
    
    # Mine initial block
    blockchain.mine_pending_transactions()
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)