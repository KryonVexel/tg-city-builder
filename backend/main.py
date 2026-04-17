from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from . import models, database
from datetime import datetime, timedelta
import hmac
import hashlib
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = FastAPI(title="CityState API")

# Initialize DB on startup
@app.on_event("startup")
def startup():
    database.init_db()

# --- Auth Helper ---
def verify_telegram_auth(init_data: str):
    """Verifies Telegram Mini App initData"""
    if not init_data:
        raise HTTPException(status_code=401, detail="Missing initData")
    
    # Implementation of validation logic as per Telegram docs
    # For now, we return a mock user ID for development
    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data))
        # Actual validation would go here
        import json
        user_data = json.loads(parsed_data.get("user", "{}"))
        return user_data.get("id")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid initData")

# --- Game Logic Helpers ---
def calculate_resources(city: models.City, db: Session):
    """Updates resources based on time elapsed since last tick/action"""
    now = datetime.utcnow()
    
    for building in city.buildings:
        hours_passed = (now - building.last_tick).total_seconds() / 3600.0
        if hours_passed >= 1.0:
            if building.type == "FARM":
                city.food += building.level * 10 * hours_passed
            elif building.type == "MINE":
                city.stone += building.level * 5 * hours_passed
            elif building.type == "MINT":
                city.gold += building.level * 50 * hours_passed
            
            building.last_tick = now
    
    # Population health check
    if city.food <= 0 or city.water <= 0:
        city.health = max(0, city.health - 1.0)
    
    # Tax Check (handled separately or on first login of the day)
    days_since_tax = (now - city.tax_last_collected).days
    if days_since_tax >= 1:
        # 1 coin per 16x16 square owned
        # For now, let's assume city owns 1 square by default
        tax_amount = 1.0 * days_since_tax
        city.gold -= tax_amount
        city.tax_last_collected = now
        
    db.commit()

# --- API Endpoints ---

@app.get("/city")
def get_city(init_data: str = Header(None), db: Session = Depends(database.get_db)):
    tg_id = verify_telegram_auth(init_data)
    user = db.query(models.User).filter(models.User.telegram_id == tg_id).first()
    
    if not user:
        # Auto-registration for dev
        user = models.User(telegram_id=tg_id)
        db.add(user)
        db.commit()
    
    membership = db.query(models.CityMember).filter(models.CityMember.user_id == user.id).first()
    if not membership:
        return {"status": "no_city"}
    
    city = membership.city
    calculate_resources(city, db)
    
    return {
        "city": {
            "name": city.name,
            "gold": round(city.gold, 2),
            "food": round(city.food, 2),
            "water": round(city.water, 2),
            "stone": round(city.stone, 2),
            "population": city.population,
            "health": city.health,
            "role": membership.role
        },
        "buildings": [
            {"type": b.type, "level": b.level, "x": b.grid_x, "y": b.grid_y}
            for b in city.buildings
        ]
    }

@app.post("/create_city")
def create_city(name: str, x: int, y: int, init_data: str = Header(None), db: Session = Depends(database.get_db)):
    tg_id = verify_telegram_auth(init_data)
    user = db.query(models.User).filter(models.User.telegram_id == tg_id).first()
    
    # Check if city at x,y is taken
    existing = db.query(models.City).filter(models.City.x == x, models.City.y == y).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tile occupied")
        
    new_city = models.City(name=name, x=x, y=y)
    db.add(new_city)
    db.commit()
    
    member = models.CityMember(user_id=user.id, city_id=new_city.id, role="MAYOR")
    db.add(member)
    
    # Initial buildings
    farm = models.Building(city_id=new_city.id, type="FARM", grid_x=0, grid_y=0)
    db.add(farm)
    
    db.commit()
    return {"status": "success", "city_id": new_city.id}

@app.post("/build")
def build_building(type: str, x: int, y: int, init_data: str = Header(None), db: Session = Depends(database.get_db)):
    tg_id = verify_telegram_auth(init_data)
    user = db.query(models.User).filter(models.User.telegram_id == tg_id).first()
    membership = db.query(models.CityMember).filter(models.CityMember.user_id == user.id).first()
    
    if not membership:
        raise HTTPException(status_code=400, detail="No city")
    
    city = membership.city
    
    # Check if tile occupied in city grid (0-9 range)
    existing = db.query(models.Building).filter(models.Building.city_id == city.id, 
                                               models.Building.grid_x == x, 
                                               models.Building.grid_y == y).first()
    if existing:
        raise HTTPException(status_code=400, detail="Building already there")
        
    # Cost check
    costs = {"FARM": 0, "MINE": 100, "MINT": 500, "HOUSE": 50}
    cost = costs.get(type, 0)
    
    if city.gold < cost:
        raise HTTPException(status_code=400, detail="Not enough gold")
        
    city.gold -= cost
    new_building = models.Building(city_id=city.id, type=type, grid_x=x, grid_y=y)
    db.add(new_building)
    db.commit()
    
    return {"status": "success"}

@app.get("/map")
def get_map(db: Session = Depends(database.get_db)):
    cities = db.query(models.City).all()
    return [
        {"id": c.id, "name": c.name, "x": c.x, "y": c.y}
        for c in cities
    ]

# Подключаем раздачу статики (frontend)
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
