let blockchain = [];
let products = [];

document.addEventListener('DOMContentLoaded', () => {
    loadBlockchain();
    loadProducts();
    populateDropdowns();
});

async function loadBlockchain() {
    try {
        const res = await fetch('/api/blockchain');
        blockchain = await res.json();
        renderBlockchain();
    } catch (err) {
        console.error('Error loading blockchain:', err);
    }
}

async function loadProducts() {
    try {
        const res = await fetch('/api/all_products');
        products = await res.json();
        renderProducts();
        renderProductPanel();
    } catch (err) {
        console.error('Error loading products:', err);
    }
}

async function populateDropdowns() {
    try {
        const res = await fetch('/api/network');
        const data = await res.json();
        const fromSelect = document.getElementById('from');
        const toSelect = document.getElementById('to');

        data.nodes.forEach(node => {
            fromSelect.appendChild(new Option(node.label, node.id));
            toSelect.appendChild(new Option(node.label, node.id));
        });
    } catch (err) {
        console.error('Failed to populate dropdowns:', err);
    }
}

async function createProduct() {
    const name = document.getElementById('name').value;
    const id = document.getElementById('product-id').value;
    const from = document.getElementById('from').value;
    const to = document.getElementById('to').value;
    const metric = document.getElementById('metric').value;

    if (!name || !id || !from || !to || !metric) return;

    try {
        const res = await fetch('/api/create_product', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, product_id: id, from, to, metric })
        });

        const data = await res.json();
        if (data.success) loadProducts();
    } catch (err) {
        console.error('Error creating product:', err);
    }
}

async function mineBlock() {
    try {
        const res = await fetch('/api/mine');
        const data = await res.json();
        if (data.success) loadBlockchain();
    } catch (err) {
        console.error('Error mining block:', err);
    }
}

function renderBlockchain() {
    const el = document.getElementById('blockchain');
    if (!el) return;

    el.innerHTML = blockchain.map((b, i) => `
        <div class="panel" onclick="showBlockDetails(${i})">
            <h2>Block #${b.index}</h2>
            <p><strong>Prev Hash:</strong> ${b.prev_hash}</p>
            <p><strong>Next Hash:</strong> ${b.hash}</p>
        </div>
    `).join('');
}

function showBlockDetails(index) {
    const b = blockchain[index];
    if (!b) return;

    const nextHash = blockchain[index + 1]?.hash || "None";
    const isValid = index === blockchain.length - 1 || blockchain[index + 1].prev_hash === b.hash;
    const firstTx = b.transactions[0] || {};

    const panel1 = `
        <div class="panel">
            <h2>Block #${b.index}</h2>
            <p><strong>Timestamp:</strong> ${new Date(b.timestamp).toLocaleString()}</p>
            <p><strong>Prev Hash:</strong> ${b.prev_hash}</p>
            <p><strong>Next Hash:</strong> ${nextHash}</p>
        </div>
    `;

    const panel2 = `
        <div class="panel">
            <h3>Transaction Details</h3>
            <p><strong>Product ID:</strong> ${firstTx.product_id || firstTx.id || 'N/A'}</p>
            <p><strong>Product Name:</strong> ${firstTx.name || 'N/A'}</p>
            <p>
                ${b.transactions.map(t => `
                    <strong>Transaction Path:</strong> ${t.path?.join(' → ') || `${t.from} → ${t.to}`}
                `).join('<br>')}
            </p>
            <p><strong>Status:</strong> ${isValid ? 'Valid' : 'Not Valid'}</p>
            <p><strong>Transaction Success:</strong> ${isValid ? '✅' : '❌'}</p>
        </div>
    `;

    const html = `
    <div class="block-details">
        ${panel1}
        ${panel2}
    </div>
    `;

    document.getElementById('block-details').innerHTML = html;
}

function renderProducts() {
    const el = document.getElementById('products');
    if (!el) return;

    el.innerHTML = products.map(p => `
        <div class="panel">
            <h2>${p.name}</h2>
            <p><strong>ID:</strong> ${p.product_id || p.id}</p>
            <p><strong>Location:</strong> ${p.from}</p>
        </div>
    `).join('');
}

function renderProductPanel() {
    const container = document.getElementById('product-panel');
    if (!container || !products.length) return;

    const productBoxes = products.map(p => `
        <div class="product-box">
            <p><strong>Name:</strong> ${p.name}</p>
            <p><strong>ID:</strong> ${p.product_id || p.id}</p>
            <p><strong>From:</strong> ${p.from}</p>
            <p><strong>To:</strong> ${p.to}</p>
        </div>
    `).join('');

    container.innerHTML = `
        <div class="panel">
            <h3>All Products</h3>
            <div class="product-scroll">
                ${productBoxes}
            </div>
        </div>
    `;
}

window.showBlockDetails = showBlockDetails;