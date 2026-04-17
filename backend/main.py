from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, database
from datetime import datetime, timedelta
import hmac
import hashlib
import urllib.parse
import os
import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = FastAPI(title="CityState API")

# CORS middleware for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    database.init_db()

def verify_telegram_auth(init_data: str):
    """Verifies Telegram Mini App initData"""
    if not init_data:
        raise HTTPException(status_code=401, detail="Missing initData")
    
    # Dev mode fallback
    if init_data == "user=%7B%22id%22%3A12345%2C%22first_name%22%3A%22Dev%22%7D":
        return 12345
        
    if not BOT_TOKEN:
        try:
            parsed = dict(urllib.parse.parse_qsl(init_data))
            user_data = json.loads(parsed.get("user", "{}"))
            return user_data.get("id", 12345)
        except:
            raise HTTPException(status_code=401, detail="Invalid initData")
            
    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data))
        hash_val = parsed_data.pop("hash", None)
        if not hash_val:
            raise ValueError()

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated_hash != hash_val:
            raise ValueError()
            
        user_data = json.loads(parsed_data.get("user", "{}"))
        return user_data.get("id")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid initData Signature")

def calculate_resources(city: models.City, db: Session):
    """Updates resources based on time elapsed since last tick"""
    now = datetime.utcnow()
    
    for building in city.buildings:
        hours_passed = (now - building.last_tick).total_seconds() / 3600.0
        # Give resources if at least 30 seconds have passed (0.0083 hours)
        if hours_passed >= 0.0083:
            if building.type == "FARM":
                city.food += building.level * 10 * hours_passed
            elif building.type == "MINE":
                city.stone += building.level * 5 * hours_passed
            elif building.type == "MINT":
                city.gold += building.level * 50 * hours_passed
            
            building.last_tick = now
    
    db.commit()

@app.get("/city")
def get_city(init_data: str = Header(None), db: Session = Depends(database.get_db)):
    tg_id = verify_telegram_auth(init_data)
    user = db.query(models.User).filter(models.User.telegram_id == tg_id).first()
    
    if not user:
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
    
    if not user:
        user = models.User(telegram_id=tg_id)
        db.add(user)
        db.commit()

    existing = db.query(models.City).filter(models.City.x == x, models.City.y == y).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tile occupied")
        
    new_city = models.City(name=name, x=x, y=y)
    db.add(new_city)
    db.commit()
    
    member = models.CityMember(user_id=user.id, city_id=new_city.id, role="MAYOR")
    db.add(member)
    
    # Place initial building in the center
    farm = models.Building(city_id=new_city.id, type="FARM", grid_x=4, grid_y=4)
    db.add(farm)
    
    db.commit()
    return {"status": "success", "city_id": new_city.id}

@app.post("/build")
def build_building(type: str, x: int, y: int, init_data: str = Header(None), db: Session = Depends(database.get_db)):
    tg_id = verify_telegram_auth(init_data)
    user = db.query(models.User).filter(models.User.telegram_id == tg_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    membership = db.query(models.CityMember).filter(models.CityMember.user_id == user.id).first()
    
    if not membership:
        raise HTTPException(status_code=400, detail="No city")
    
    city = membership.city
    calculate_resources(city, db)
    
    existing = db.query(models.Building).filter(models.Building.city_id == city.id, 
                                               models.Building.grid_x == x, 
                                               models.Building.grid_y == y).first()
    if existing:
        raise HTTPException(status_code=400, detail="Building already there")
        
    costs = {"FARM": 0, "MINE": 100, "MINT": 500, "HOUSE": 50}
    cost = costs.get(type, 0)
    
    if city.gold < cost:
        raise HTTPException(status_code=400, detail="Not enough gold")
        
    city.gold -= cost
    if type == "HOUSE":
        city.population += 5
        
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

# Serve frontend static files
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
