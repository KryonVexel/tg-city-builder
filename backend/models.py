from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, PRIMARY KEY=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, DEFAULT=datetime.datetime.utcnow)

    city_memberships = relationship("CityMember", back_populates="user")

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, PRIMARY KEY=True, index=True)
    name = Column(String, unique=True)
    
    # Resources
    gold = Column(Float, DEFAULT=1000.0)
    food = Column(Float, DEFAULT=500.0)
    water = Column(Float, DEFAULT=500.0)
    stone = Column(Float, DEFAULT=200.0)
    
    # Stats
    population = Column(Integer, DEFAULT=10)
    health = Column(Float, DEFAULT=100.0)
    
    # Map Position (16x16 coordinate system)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    
    tax_last_collected = Column(DateTime, DEFAULT=datetime.datetime.utcnow)
    created_at = Column(DateTime, DEFAULT=datetime.datetime.utcnow)

    members = relationship("CityMember", back_populates="city")
    buildings = relationship("Building", back_populates="city")

class CityMember(Base):
    __tablename__ = "city_members"
    user_id = Column(Integer, ForeignKey("users.id"), PRIMARY KEY=True)
    city_id = Column(Integer, ForeignKey("cities.id"), PRIMARY KEY=True)
    
    role = Column(String, DEFAULT="RESIDENT") # MAYOR, VICE_MAYOR, RESIDENT
    permissions = Column(JSON, nullable=True) # Specific rights like "can_build", "can_withdraw"
    
    user = relationship("User", back_populates="city_memberships")
    city = relationship("City", back_populates="members")

class Building(Base):
    __tablename__ = "buildings"
    id = Column(Integer, PRIMARY KEY=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"))
    
    type = Column(String) # FARM, MINE, MINT, HOUSE, DECO
    level = Column(Integer, DEFAULT=1)
    
    # Local grid position
    grid_x = Column(Integer)
    grid_y = Column(Integer)
    
    last_tick = Column(DateTime, DEFAULT=datetime.datetime.utcnow)
    
    city = relationship("City", back_populates="buildings")

class MapTile(Base):
    __tablename__ = "map_tiles"
    x = Column(Integer, PRIMARY KEY=True)
    y = Column(Integer, PRIMARY KEY=True)
    
    owner_city_id = Column(Integer, ForeignKey("cities.id"), nullable=True)
    type = Column(String, DEFAULT="plains") # forest, mountain, desert, plains
    
    __table_args__ = (UniqueConstraint('x', 'y', name='_coords_uc'),)

class Mission(Base):
    __tablename__ = "missions"
    id = Column(Integer, PRIMARY KEY=True, index=True)
    attacker_city_id = Column(Integer, ForeignKey("cities.id"))
    defender_city_id = Column(Integer, ForeignKey("cities.id"))
    
    start_time = Column(DateTime, DEFAULT=datetime.datetime.utcnow)
    end_time = Column(DateTime)
    
    status = Column(String, DEFAULT="PENDING") # PENDING, COMPLETED, CANCELLED
    result = Column(JSON, nullable=True)

class MarketListing(Base):
    __tablename__ = "market_listings"
    id = Column(Integer, PRIMARY KEY=True, index=True)
    seller_city_id = Column(Integer, ForeignKey("cities.id"))
    
    item_type = Column(String)
    stats = Column(JSON)
    price = Column(Float)
    
    created_at = Column(DateTime, DEFAULT=datetime.datetime.utcnow)
