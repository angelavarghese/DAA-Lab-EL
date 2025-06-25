document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
    fetch('/network-data')
        .then(res => res.json())
        .then(data => {
            if (data.nodes) loadNodeTypeChart(data.nodes);
        })
        .catch(err => console.error("Failed to load network data:", err));
    loadArticulationPoints();
    loadNetworkStats();
});

async function loadDashboardStats() {
    try {
        const [blockRes, productRes] = await Promise.all([
            fetch('/api/blockchain'),
            fetch('/api/all_products')
        ]);
        const blocks = await blockRes.json();
        const products = await productRes.json();

        const totalTransactions = blocks.reduce((acc, block) => acc + block.transactions.length, 0);
        const pendingShipments = products.length;
        const verifiedProducts = 100 + totalTransactions;
        const blockCount = blocks.length;

        renderCards({ totalTransactions, blockCount, pendingShipments, verifiedProducts });
    } catch (err) {
        console.error('Dashboard stats error:', err);
    }
}

function renderCards(stats) {
    const container = document.getElementById('dashboard-cards');
    container.innerHTML = '';

    const cardData = [
        { title: 'Total Transactions', value: stats.totalTransactions },
        { title: 'Blocks in Chain', value: stats.blockCount },
        { title: 'Pending Shipments', value: stats.pendingShipments },
        { title: 'Verified Products', value: stats.verifiedProducts }
    ];

    cardData.forEach(card => {
        const div = document.createElement('div');
        div.className = 'card';
        div.innerHTML = `<strong>${card.title}</strong><br><span style="font-size:1.8rem;">${card.value}</span>`;
        container.appendChild(div);
    });
}

function loadNodeTypeChart(nodes) {
    const counts = {};
    nodes.forEach(node => {
        const type = node.type;
        counts[type] = (counts[type] || 0) + 1;
    });

    const ctx = document.getElementById('nodeTypeChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(counts),
            datasets: [{
                label: 'Node Types',
                data: Object.values(counts),
                backgroundColor: [
                    '#493D9E', '#B2A5FF', '#DAD2FF', '#FFF2AF', '#FFD6A5', '#A0C4FF'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'right' },
                tooltip: {
                    callbacks: {
                        label: context => `${context.label || ''}: ${context.raw || 0}`
                    }
                }
            }
        }
    });
}

async function loadArticulationPoints() {
    try {
        const res = await fetch('/api/articulation_points');
        const data = await res.json();
        document.getElementById('ap-count').textContent = data.count;
        document.getElementById('ap-list').textContent = data.points.join(', ');
    } catch (err) {
        console.error('Failed to load articulation points:', err);
    }
}

async function loadNetworkStats() {
    try {
        const res = await fetch('/api/network_stats');
        const data = await res.json();
        document.getElementById('node-count').innerHTML = `<strong>Total Nodes</strong><br><span style="font-size:1.8rem;">${data.node_count}</span>`;
        document.getElementById('avg-cost').innerHTML = `<strong>Avg. Cost</strong><br><span style="font-size:1.8rem;">${data.avg_cost}</span>`;
        document.getElementById('avg-time').innerHTML = `<strong>Avg. Time</strong><br><span style="font-size:1.8rem;">${data.avg_time}</span>`;
    } catch (err) {
        console.error('Failed to load network stats:', err);
    }
}
