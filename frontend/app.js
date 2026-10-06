// Alternância de Abas na Autenticação (Login / Cadastro)
function switchAuthTab(mode) {
    const btnLogin = document.querySelectorAll('.auth-tab-btn')[0];
    const btnCadastro = document.querySelectorAll('.auth-tab-btn')[1];
    const formLogin = document.getElementById('form-login');
    const formCadastro = document.getElementById('form-cadastro');

    if (mode === 'login') {
        btnLogin.classList.add('active');
        btnCadastro.classList.remove('active');
        formLogin.classList.remove('hidden');
        formCadastro.classList.add('hidden');
    } else {
        btnCadastro.classList.add('active');
        btnLogin.classList.remove('active');
        formCadastro.classList.remove('hidden');
        formLogin.classList.add('hidden');
    }
}

// Lógica de Login
function handleLogin(event) {
    event.preventDefault();
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('hidden');
}

// Lógica de Cadastro
function handleRegister(event) {
    event.preventDefault();
    alert("Cadastro realizado com sucesso! Acessando área protegida...");
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('hidden');
}

function logout() {
    if (typeof pararRastreamento === 'function') pararRastreamento();
    document.getElementById('app-screen').classList.add('hidden');
    document.getElementById('disguise-screen').classList.add('hidden');
    document.getElementById('auth-screen').classList.remove('hidden');
}

// Navegação entre abas do Painel
function switchTab(event, tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.querySelectorAll('.sidebar-btn').forEach(btn => btn.classList.remove('active'));

    document.getElementById(tabId).classList.remove('hidden');
    event.currentTarget.classList.add('active');
}

// Modo Disfarce
function toggleDisguise() {
    document.getElementById('app-screen').classList.toggle('hidden');
    document.getElementById('disguise-screen').classList.toggle('hidden');
}

// =======================================================================
// GEOLOCALIZAÇÃO EM TEMPO REAL E DISPARO DE EMERGÊNCIA
// =======================================================================
let watchId = null;

function iniciarRastreamento() {
    if (!('geolocation' in navigator)) {
        alert('Geolocalização não é suportada pelo seu navegador.');
        return;
    }

    const opcoes = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
    };

    watchId = navigator.geolocation.watchPosition(
        (posicao) => {
            const lat = posicao.coords.latitude;
            const lng = posicao.coords.longitude;
            const statusBadge = document.getElementById('alert-status');
            
            if (statusBadge) {
                statusBadge.innerHTML = `● ALERTA ATIVO — Geolocalização (${lat.toFixed(4)}, ${lng.toFixed(4)}) registrada e transmitida para contatos de confiança.`;
            }
            
            window.localizacaoAtual = {
                lat,
                lng,
                linkMaps: `https://maps.google.com/?q=${lat},${lng}`
            };
        },
        (erro) => {
            console.error('Erro na localização:', erro.message);
            const statusBadge = document.getElementById('alert-status');
            if (statusBadge) {
                statusBadge.innerHTML = `⚠️ Falha ao obter localização: ${erro.message}`;
            }
        },
        opcoes
    );
}

function pararRastreamento() {
    if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
    }
}

// Disparo de Emergência - Solicita permissão e ativa a localização ao clicar no botão
function triggerAlert() {
    const statusBadge = document.getElementById('alert-status');
    statusBadge.classList.remove('hidden');
    iniciarRastreamento();
}

// Anexo de Provas (Geração Simulada de Hash SHA-256)
function uploadProof() {
    const input = document.getElementById('file-input');
    const list = document.getElementById('proof-list');

    if (input.files.length > 0) {
        const fileName = input.files[0].name;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${fileName}</td>
            <td>Agora</td>
            <td><code>8f434346648f6b96df89dda901c5176b10a6d83961dd3c1a...</code></td>
        `;
        list.appendChild(row);
        input.value = '';
    }
}

// Chat RAG Local
function sendMessage() {
    const input = document.getElementById('chat-input');
    const chatBox = document.getElementById('chat-box');

    if (input.value.trim() !== '') {
        const userMsg = document.createElement('div');
        userMsg.className = 'chat-msg user';
        userMsg.innerText = input.value;
        chatBox.appendChild(userMsg);

        const query = input.value.toLowerCase();
        input.value = '';

        setTimeout(() => {
            const sysMsg = document.createElement('div');
            sysMsg.className = 'chat-msg system';

            if (query.includes('delegacia') || query.includes('maringá') || query.includes('onde')) {
                sysMsg.innerText = "DEAM Maringá: Av. Mandacaru, 280 - Vila Santa Izabel. Atendimento para registro de ocorrência e suporte.";
            } else if (query.includes('medida') || query.includes('protetiva')) {
                sysMsg.innerText = "Medidas protetivas podem ser requeridas na DEAM e determinam o afastamento do agressor.";
            } else {
                sysMsg.innerText = "Em situações de emergência iminente, contate o 190 (Polícia Militar) ou 180.";
            }

            chatBox.appendChild(sysMsg);
            chatBox.scrollTop = chatBox.scrollHeight;
        }, 400);
    }
}

// Adicionar Contato de Confiança
function addContact() {
    const name = document.getElementById('new-contact-name').value;
    const phone = document.getElementById('new-contact-phone').value;
    const list = document.getElementById('contact-list');

    if (name && phone) {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${name}</td><td>Contato de Confiança</td><td>${phone}</td>`;
        list.appendChild(row);
        document.getElementById('new-contact-name').value = '';
        document.getElementById('new-contact-phone').value = '';
    }
}

// Lógica do Cardápio (Modo Disfarce)
let cart = [];
let total = 0;

function filterCategory(cat) {
    document.querySelectorAll('.cat-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    document.querySelectorAll('.dish-card').forEach(card => {
        if (cat === 'todos' || card.dataset.cat === cat) {
            card.classList.remove('hidden');
        } else {
            card.classList.add('hidden');
        }
    });
}

function addToCart(title, price) {
    cart.push({ title, price });
    total += price;
    updateCartUI();
}

function updateCartUI() {
    const cartList = document.getElementById('cart-items');
    const totalElement = document.getElementById('cart-total-value');

    cartList.innerHTML = '';
    cart.forEach(item => {
        const li = document.createElement('li');
        li.className = 'cart-item';
        li.innerHTML = `<span>${item.title}</span> <strong>R$ ${item.price.toFixed(2)}</strong>`;
        cartList.appendChild(li);
    });

    totalElement.innerText = `R$ ${total.toFixed(2)}`;
}

function sendOrder() {
    if (cart.length > 0) {
        alert("Pedido enviado para a cozinha com sucesso!");
        cart = [];
        total = 0;
        updateCartUI();
        document.getElementById('cart-items').innerHTML = '<li style="color: var(--menu-text-muted); font-size: 0.85rem;">Seu pedido está vazio.</li>';
    } else {
        alert("Selecione ao menos um item no cardápio antes de enviar.");
    }
}

// =======================================================================
// INTEGRACAO PWA: REGISTRO E ATALHO NA TELA INICIAL
// =======================================================================
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js')
            .then(reg => console.log('Service Worker registrado:', reg))
            .catch(err => console.error('Erro no SW:', err));
    });
}

let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    const btnInstalar = document.getElementById('btn-instalar-atalho');
    if (btnInstalar) {
        btnInstalar.classList.remove('hidden');
        btnInstalar.addEventListener('click', () => {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('Usuária instalou o atalho na tela inicial.');
                }
                deferredPrompt = null;
                btnInstalar.classList.add('hidden');
            });
        });
    }
});