const tg = window.Telegram.WebApp;
tg.expand();

const API_URL = "http://localhost:8000"; // Замените на реальный URL при деплое
let initData = tg.initData || "user=%7B%22id%22%3A12345%2C%22first_name%22%3A%22Dev%22%7D";

let cityData = null;

// Инициализация
async function init() {
    await fetchCity();
    renderGrid();
    setInterval(fetchCity, 60000); // Обновлять ресурсы каждую минуту
}

async function fetchCity() {
    try {
        const res = await fetch(`${API_URL}/city`, {
            headers: { 'init-data': initData }
        });
        const data = await res.json();
        
        if (data.status === "no_city") {
            createStartCity();
        } else {
            cityData = data;
            updateUI();
        }
    } catch (e) {
        console.error("Ошибка загрузки города:", e);
    }
}

async function createStartCity() {
    const cityName = prompt("Как назовем твой город?", "Камелот");
    if (!cityName) return;
    
    // Выбираем случайные координаты для начала (упрощение)
    const x = Math.floor(Math.random() * 100);
    const y = Math.floor(Math.random() * 100);
    
    await fetch(`${API_URL}/create_city?name=${encodeURIComponent(cityName)}&x=${x}&y=${y}`, {
        method: 'POST',
        headers: { 'init-data': initData }
    });
    fetchCity();
}

function updateUI() {
    if (!cityData) return;
    document.getElementById('gold').innerText = cityData.city.gold;
    document.getElementById('food').innerText = cityData.city.food;
    document.getElementById('stone').innerText = cityData.city.stone;
    document.getElementById('population').innerText = cityData.city.population;
    
    renderGrid();
}

function renderGrid() {
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    
    // Создаем сетку 10x10
    for(let y=0; y<10; y++) {
        for(let x=0; x<10; x++) {
            const tile = document.createElement('div');
            tile.className = 'tile';
            tile.dataset.x = x;
            tile.dataset.y = y;
            
            // Ищем здание в этой клетке
            const b = cityData?.buildings?.find(b => b.x === x && b.y === y);
            if(b) {
                tile.classList.add('building');
                tile.innerText = getBuildingEmoji(b.type);
            }
            
            tile.onclick = () => onTileClick(x, y);
            grid.appendChild(tile);
        }
    }
}

function getBuildingEmoji(type) {
    const map = { 'FARM': '🌾', 'MINE': '⚒️', 'MINT': '🏦', 'HOUSE': '🏠' };
    return map[type] || '❓';
}

function onTileClick(x, y) {
    // Открыть меню строительства, если клетка пуста
    const b = cityData?.buildings?.find(b => b.x === x && b.y === y);
    if (!b) {
        window.selectedTile = {x, y};
        document.getElementById('build-modal').classList.remove('hidden');
    }
}

function showView(view) {
    document.getElementById('city-view').classList.toggle('hidden', view !== 'city');
    document.getElementById('map-view').classList.toggle('hidden', view !== 'map');
    
    if (view === 'build') {
        document.getElementById('build-modal').classList.remove('hidden');
    }
}

function closeModal() {
    document.getElementById('build-modal').classList.add('hidden');
}

async function build(type) {
    if (!window.selectedTile) return;
    const {x, y} = window.selectedTile;
    
    try {
        const res = await fetch(`${API_URL}/build?type=${type}&x=${x}&y=${y}`, {
            method: 'POST',
            headers: { 'init-data': initData }
        });
        const data = await res.json();
        if (data.status === "success") {
            closeModal();
            fetchCity();
        } else {
            alert(data.detail || "Ошибка строительства");
        }
    } catch (e) {
        alert("Ошибка сети");
    }
}

