let networkData = {};
let companies = {};

document.addEventListener('DOMContentLoaded', () => {
    loadNetwork();
    loadProductCards(); // call this on page load
});

async function loadNetwork() {
    try {
        const res = await fetch('/api/network');
        networkData = await res.json();
        initializeNetwork();
        calculateNetworkStats(networkData);
    } catch (err) {
        console.error('Error loading network:', err);
    }
}

function initializeNetwork() {
    const container = document.getElementById('network-vis');



    if (!container) return;

    const nodes = new vis.DataSet(networkData.nodes.map(node => ({
        id: node.id,
        label: node.label,
        title: `${node.label} (${node.type})`,
        shape: "box",
        borderRadius: 8, // not officially supported, but keep for fallback
        widthConstraint: { minimum: 100 },
        heightConstraint: { minimum: 10 },
        color: {
            background: getNodeColor(node.type),
            border: "#333",
            highlight: {
                background: "#fff",
                border: "#000"
            }
        },
        font: { color: "#000", size: 14 },
        margin: 10
    })));


    const edges = new vis.DataSet(networkData.edges.map(edge => ({
        from: edge.from,
        to: edge.to,
        label: edge.cost.toString(),
        arrows: {
            to: {
                enabled: true,
                scaleFactor: 0.5  // adjust between 0.3 to 0.7 as needed
            }
        }
    })));

    new vis.Network(container, { nodes, edges }, {
        physics: true,
        layout: { hierarchical: false }
    });

    networkData.nodes.forEach(n => companies[n.id] = n);

    const network = new vis.Network(container, { nodes, edges }, {
        physics: true,
        layout: { hierarchical: false }
    });

    // Set zoom level (1 = default)
    network.moveTo({ scale: 0.75 });
}

function getNodeColor(type) {
    return {
        "supplier": '#493D9E',
        "manufacturer": '#B2A5FF',
        "distributor": '#DAD2FF',
        "retailer": '#9FC87E',
        "Supplier": '#C599B6',
        "Processing Unit": '#BFECFF',
        "Manufacturer": '#DAD2FF',
        "Distributor": '#9FC87E',
        "Consumer": '#FFF2E0',
    }[type] || '#999';
}

async function calculateNetworkStats(data) {
    const nodes = data.nodes || [];
    const edges = data.edges || [];

    const start = performance.now();

    // Dijkstra from every node to every other node
    let pathsFound = 0;
    let totalCost = 0;
    const graph = {};
    nodes.forEach(n => graph[n.id] = []);
    edges.forEach(e => graph[e.from].push({ to: e.to, cost: e.cost }));

    function dijkstra(source) {
        const dist = {};
        const visited = {};
        nodes.forEach(n => dist[n.id] = Infinity);
        dist[source] = 0;

        const pq = [{ id: source, cost: 0 }];
        while (pq.length) {
            pq.sort((a, b) => a.cost - b.cost);
            const { id } = pq.shift();
            if (visited[id]) continue;
            visited[id] = true;
            for (const edge of graph[id]) {
                const newCost = dist[id] + edge.cost;
                if (newCost < dist[edge.to]) {
                    dist[edge.to] = newCost;
                    pq.push({ id: edge.to, cost: newCost });
                }
            }
        }
        return dist;
    }

    nodes.forEach(src => {
        const dist = dijkstra(src.id);
        nodes.forEach(dest => {
            if (src.id !== dest.id && dist[dest.id] < Infinity) {
                pathsFound++;
                totalCost += dist[dest.id];
            }
        });
    });

    const end = performance.now();
    const time = ((end - start) / 1000).toFixed(4);

    document.getElementById('nodes-evaluated').textContent = nodes.length;
    document.getElementById('paths-found').textContent = pathsFound;
    document.getElementById('comp-time').textContent = `${time}s`;

    document.getElementById('total-routes').textContent = pathsFound;
    document.getElementById('optimal-routes').textContent = pathsFound;
    document.getElementById('cost-reduction').textContent = '0%';

    document.getElementById('active-nodes').textContent = nodes.length;
    document.getElementById('net-health').textContent =
        isStronglyConnected(graph, nodes) ? 'Healthy' : 'Disconnected';
}

function isStronglyConnected(graph, nodes) {
    const visited = new Set();

    function dfs(v, seen) {
        seen.add(v);
        (graph[v] || []).forEach(e => {
            if (!seen.has(e.to)) dfs(e.to, seen);
        });
    }

    dfs(nodes[0].id, visited);
    return visited.size === nodes.length;
}

async function loadProductCards() {
    try {
        const res = await fetch('/api/all_products');
        const products = await res.json();

        const container = document.getElementById('product-cards');
        if (!container) return;

        container.innerHTML = products.map(p => `
      <div class="product-card">
        <p><strong>Product Name:</strong> ${p.name}</p>
        <p><strong>ID:</strong> ${p.id || p.product_id}</p>
        <p><strong>Path:</strong> ${p.path?.join(' → ') || `${p.from} → ${p.to}`}</p>
        <p><strong>Metric Used:</strong> ${p.metric}</p>
      </div>
    `).join('');
    } catch (err) {
        console.error('Failed to load product cards:', err);
    }
}
