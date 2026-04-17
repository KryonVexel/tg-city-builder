const tg = window.Telegram.WebApp;
tg.expand();
// Устанавливаем цвет хедера и фона из темы Telegram, если нужно, или фиксируем наши
tg.setHeaderColor('#0f1115');
tg.setBackgroundColor('#0f1115');

const API_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" 
    ? "http://localhost:8000" 
    : window.location.origin;

let initData = tg.initData || "user=%7B%22id%22%3A12345%2C%22first_name%22%3A%22Dev%22%7D";
let cityData = null;

// Инициализация
async function init() {
    await fetchCity();
    setInterval(fetchCity, 30000); // Обновлять ресурсы каждые 30 сек
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
        tg.showAlert("Не удалось загрузить данные города.");
    }
}

async function createStartCity() {
    tg.showPopup({
        title: "Основание города",
        message: "Готовы заложить первый камень вашего королевства?",
        buttons: [{id: "create", type: "default", text: "Да, начнем!"}]
    }, async (buttonId) => {
        if (buttonId === "create") {
            const cityName = "Камелот " + Math.floor(Math.random() * 1000);
            const x = Math.floor(Math.random() * 100);
            const y = Math.floor(Math.random() * 100);
            
            try {
                await fetch(`${API_URL}/create_city?name=${encodeURIComponent(cityName)}&x=${x}&y=${y}`, {
                    method: 'POST',
                    headers: { 'init-data': initData }
                });
                fetchCity();
            } catch (e) {
                tg.showAlert("Ошибка при создании города.");
            }
        }
    });
}

function updateUI() {
    if (!cityData) return;
    
    // Анимированное изменение чисел (опционально, здесь просто обновление)
    document.getElementById('gold').innerText = Math.floor(cityData.city.gold);
    document.getElementById('food').innerText = Math.floor(cityData.city.food);
    document.getElementById('stone').innerText = Math.floor(cityData.city.stone);
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
    const b = cityData?.buildings?.find(b => b.x === x && b.y === y);
    if (!b) {
        window.selectedTile = {x, y};
        openBuildModal();
    } else {
        tg.showAlert(`Здесь находится: ${getBuildingName(b.type)}\nУровень: ${b.level}`);
    }
}

function getBuildingName(type) {
    const map = { 'FARM': 'Ферма', 'MINE': 'Шахта', 'MINT': 'Монетный двор', 'HOUSE': 'Дом' };
    return map[type] || type;
}

// Навигация
function showView(viewId, btnElement) {
    // Скрыть все view
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    
    // Показать нужный view
    const view = document.getElementById(`${viewId}-view`);
    if(view) {
        view.classList.remove('hidden');
        // Небольшая задержка для анимации opacity
        setTimeout(() => view.classList.add('active'), 10);
    }
    
    // Обновить активную кнопку (если передана)
    if (btnElement) {
        document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
        btnElement.classList.add('active');
    }
}

// Модальное окно строительства
function openBuildModal() {
    if (!window.selectedTile) {
        tg.showAlert("Сначала выберите пустую клетку в городе!");
        return;
    }
    document.getElementById('overlay').classList.remove('hidden');
    document.getElementById('build-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('overlay').classList.add('hidden');
    document.getElementById('build-modal').classList.add('hidden');
}

async function build(type) {
    if (!window.selectedTile) return;
    const {x, y} = window.selectedTile;
    
    // Вибрация при нажатии
    if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
    
    try {
        const res = await fetch(`${API_URL}/build?type=${type}&x=${x}&y=${y}`, {
            method: 'POST',
            headers: { 'init-data': initData }
        });
        const data = await res.json();
        
        if (data.status === "success") {
            closeModal();
            window.selectedTile = null;
            if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
            await fetchCity(); // Обновляем город
        } else {
            tg.showAlert(data.detail || "Недостаточно ресурсов или клетка занята.");
            if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('error');
        }
    } catch (e) {
        tg.showAlert("Ошибка сети");
    }
}

// Запуск
document.addEventListener('DOMContentLoaded', init);
