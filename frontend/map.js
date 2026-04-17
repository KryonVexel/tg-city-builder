async function initMap() {
    const mapContainer = document.getElementById('world-map');
    mapContainer.innerHTML = '';
    
    try {
        const res = await fetch(`${API_URL}/map`);
        const cities = await res.json();
        
        // Создаем сетку 20x20 для мира (упрощенно)
        const mapGrid = document.createElement('div');
        mapGrid.className = 'world-grid';
        mapGrid.style.display = 'grid';
        mapGrid.style.gridTemplateColumns = 'repeat(20, 40px)';
        mapGrid.style.gridTemplateRows = 'repeat(20, 40px)';
        mapGrid.style.gap = '1px';
        
        for(let y=0; y<20; y++) {
            for(let x=0; x<20; x++) {
                const tile = document.createElement('div');
                tile.className = 'map-tile';
                tile.style.width = '40px';
                tile.style.height = '40px';
                tile.style.background = '#2d5a27'; // Зеленый для пустой земли
                tile.style.border = '0.1px solid rgba(255,255,255,0.1)';
                
                const city = cities.find(c => c.x === x && c.y === y);
                if(city) {
                    tile.style.background = '#8b0000'; // Красный для городов
                    tile.title = city.name;
                    tile.innerHTML = '🏰';
                    tile.style.display = 'flex';
                    tile.style.alignItems = 'center';
                    tile.style.justifyContent = 'center';
                }
                
                mapGrid.appendChild(tile);
            }
        }
        mapContainer.appendChild(mapGrid);
    } catch (e) {
        console.error("Ошибка загрузки карты:", e);
    }
}

// Вызываем при переключении на карту
function showView(view) {
    document.getElementById('city-view').classList.toggle('hidden', view !== 'city');
    document.getElementById('map-view').classList.toggle('hidden', view !== 'map');
    
    if (view === 'map') {
        initMap();
    }
    
    if (view === 'build') {
        document.getElementById('build-modal').classList.remove('hidden');
    }
}
