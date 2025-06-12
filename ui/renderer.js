let customers = [];
let filtered = [];
let selectedIdx = null;

const listDiv = document.getElementById('customer-list');
const searchInput = document.getElementById('search');
const addBtn = document.getElementById('add-btn');
const form = document.getElementById('customer-form');
const emptyState = document.getElementById('empty-state');

const fields = ['canonical', 'status', 'packed_products', 'shipped', 'master_order_list', 'mon_customer_ms', 'aliases'];

function renderList() {
    listDiv.innerHTML = '';
    filtered.forEach((c, i) => {
        const div = document.createElement('div');
        div.className = 'customer-item' + (i === selectedIdx ? ' selected' : '');
        div.textContent = c.canonical;
        div.onclick = () => selectCustomer(i);
        listDiv.appendChild(div);
    });
}

function selectCustomer(idx) {
    selectedIdx = idx;
    renderList();
    const c = filtered[idx];
    form.style.display = 'block';
    emptyState.style.display = 'none';
    fields.forEach(f => {
        if (f === 'aliases') {
            form[f].value = (c.aliases || []).join(', ');
        } else {
            form[f].value = c[f] || '';
        }
    });
}

function clearForm() {
    form.reset();
    form.style.display = 'none';
    emptyState.style.display = 'block';
    selectedIdx = null;
}

function filterList() {
    const q = searchInput.value.toLowerCase();
    filtered = customers.filter(c => c.canonical.toLowerCase().includes(q) || (c.aliases || []).some(a => a.toLowerCase().includes(q)));
    renderList();
    clearForm();
}

form.onsubmit = async (e) => {
    e.preventDefault();
    const obj = {};
    fields.forEach(f => {
        if (f === 'aliases') {
            obj.aliases = form[f].value.split(',').map(s => s.trim()).filter(Boolean);
        } else {
            obj[f] = form[f].value;
        }
    });
    if (selectedIdx !== null) {
        // update
        const origIdx = customers.findIndex(c => c.canonical === filtered[selectedIdx].canonical);
        customers[origIdx] = obj;
    } else {
        // add
        customers.push(obj);
    }
    await window.api.saveCustomers(customers);
    filterList();
    clearForm();
};

document.getElementById('delete-btn').onclick = async () => {
    if (selectedIdx === null) return;
    const origIdx = customers.findIndex(c => c.canonical === filtered[selectedIdx].canonical);
    if (origIdx !== -1) customers.splice(origIdx, 1);
    await window.api.saveCustomers(customers);
    filterList();
    clearForm();
};

addBtn.onclick = () => {
    clearForm();
    form.style.display = 'block';
    emptyState.style.display = 'none';
    selectedIdx = null;
};

searchInput.oninput = filterList;

window.api.loadCustomers().then(data => {
    customers = data;
    filtered = [...customers];
    renderList();
});
