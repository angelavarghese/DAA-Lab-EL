from flask import Flask, render_template, request, jsonify
import networkx as nx
import time
import hashlib
from flask_socketio import SocketIO
import json 
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

#### EXAMPLE 1 ####
# --- Supply Chain Network Data Using 50 Nodes and 200 edges ---

# with open("static/data/network_data_50node-200edge.json") as f:
#     network_data = json.load(f)

# with open("static/data/graph_edges_50node-200edge.json") as f:
#     edge_list = json.load(f)

#--------------------------------------------------------------------------------------------------#

#### EXAMPLE 2 ####
# --- Supply Chain Network Data ---

# with open("static/data/graph_nodes_eg1.json") as f:
#     nodes = json.load(f)

# with open("static/data/graph_edges_eg1.json") as f:
#     edge_list = json.load(f)

# network_data = {
#     "nodes": nodes,
#     "edges": [
#         {"from": e[0], "to": e[1], **e[2]} for e in edge_list
#     ]
# }

#--------------------------------------------------------------------------------------------------#

#### EXAMPLE 3 - METALLURGY ####
# --- Supply Chain Network ---
# with open("static/data/graph_nodes_mining.json") as f:
#     nodes = json.load(f)

# with open("static/data/graph_edges_mining.json") as f:
#     edge_list = json.load(f)

# network_data = {
#     "nodes": nodes,
#     "edges": [{"from": e[0], "to": e[1], **e[2]} for e in edge_list]
# }

#--------------------------------------------------------------------------------------------------#

#### EXAMPLE 4 - FARM ####
# --- Supply Chain Network ---
with open("static/data/graph_nodes_farm.json") as f:
    nodes = json.load(f)

with open("static/data/graph_edges_farm.json") as f:
    edge_list = json.load(f)

network_data = {
    "nodes": nodes,
    "edges": [{"from": e[0], "to": e[1], **e[2]} for e in edge_list]
}

#--------------------------------------------------------------------------------------------------#

# ⚠️ do not commment out anything, from this line on
G = nx.DiGraph()
G.add_edges_from(edge_list)

# --- In-Memory Stores ---
products = []
blockchain = []
all_products = []

# --- Pages ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/network")
def network():
    return render_template("network.html")

@app.route("/transactions")
def transactions_and_blocks():
    return render_template("blockchain.html")

# --- APIs ---
@app.route("/api/network")
def api_network():
    return jsonify(network_data)

@app.route("/api/articulation_points")
def articulation_points():
    try:
        undirected = G.to_undirected()
        points = list(nx.articulation_points(undirected))
        return jsonify({"count": len(points), "points": points})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/network_stats")
def network_stats():
    try:
        node_count = G.number_of_nodes()
        edges = G.edges(data=True)

        total_cost = sum(data.get("cost", 0) for _, _, data in edges)
        total_time = sum(data.get("time", 0) for _, _, data in edges)
        edge_count = len(edges)

        avg_cost = round(total_cost / edge_count, 2) if edge_count else 0
        avg_time = round(total_time / edge_count, 2) if edge_count else 0

        return jsonify({
            "node_count": node_count,
            "avg_cost": avg_cost,
            "avg_time": avg_time
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/network-data')
def get_network_data():
    return jsonify(network_data)


@app.route("/api/products")
def get_products():
    return jsonify(products)

@app.route("/api/all_products")
def all_products_api():
    return jsonify(all_products)

@app.route("/api/create_product", methods=["POST"])
def create_product():
    try:
        data = request.json
        source = data["from"]
        dest = data["to"]
        metric = data["metric"]

        if metric not in ["cost", "time", "distance"]:
            return jsonify({"success": False, "message": "Invalid metric"}), 400

        path = nx.dijkstra_path(G, source, dest, weight=metric)

        product = {
            "id": data["product_id"],
            "name": data["name"],
            "from": source,
            "to": dest,
            "metric": metric,
            "timestamp": time.time(),
            "path": path
        }

        products.append(product)
        all_products.append(product)

        return jsonify({"success": True})
    except Exception as e:
        print("CREATE_PRODUCT ERROR:", e)
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/mine", methods=["GET", "POST"])
def mine():
    if not products:
        return jsonify({"success": False, "message": "No transactions to mine"})

    prev_hash = blockchain[-1]["hash"] if blockchain else "0"
    block = {
        "index": len(blockchain) + 1,
        "timestamp": time.time(),
        "transactions": products.copy(),
        "prev_hash": prev_hash
    }
    block_str = str(block).encode()
    block["hash"] = hashlib.sha256(block_str).hexdigest()

    blockchain.append(block)
    products.clear()

    return jsonify({"success": True, "block": block})

@app.route("/api/blockchain")
def get_blockchain():
    return jsonify(blockchain)

# --- WebSocket ---
@socketio.on('connect')
def handle_connect():
    print("Client connected")

# --- Run ---
if __name__ == "__main__":
    socketio.run(app, debug=True)
