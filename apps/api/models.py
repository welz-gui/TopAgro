import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Date, Integer, UniqueConstraint, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

# --- NÚCLEO: FAZENDAS E USUÁRIOS ---

class Farm(Base):
    __tablename__ = "farms"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="farm")
    animals = relationship("Animal", back_populates="farm")
    lots = relationship("Lot", back_populates="farm")

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"))
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="operator") # admin, operator
    is_active = Column(Boolean, default=True)
    
    farm = relationship("Farm", back_populates="users")

# --- CADASTROS BASE ---

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    name = Column(String, nullable=False)
    city = Column(String)
    state = Column(String)
    contact = Column(String)

class Lot(Base):
    __tablename__ = "lots"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    name = Column(String, nullable=False)
    area_ha = Column(Float, default=0.0)
    capacity_ua = Column(Float, default=0.0)
    status = Column(String, default="ativo") # ativo, descanso, reforma
    
    farm = relationship("Farm", back_populates="lots")
    animals = relationship("Animal", back_populates="lot")

# --- ENTIDADE PRINCIPAL: ANIMAL ---

class Animal(Base):
    __tablename__ = "animals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"))
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    
    tag_code = Column(String, nullable=False) # Brinco
    race = Column(String, default="Nelore")
    sex = Column(String) # M ou F
    birth_date = Column(Date)
    entry_date = Column(Date, default=date.today)
    entry_weight = Column(Float)
    target_weight = Column(Float)
    status = Column(String, default="ativo") # ativo, vendido, morto, carencia
    
    # Metadados de auditoria
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    farm = relationship("Farm", back_populates="animals")
    lot = relationship("Lot", back_populates="animals")
    weighings = relationship("Weighing", back_populates="animal", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="animal")
    movements = relationship("Movement", back_populates="animal")
    costs = relationship("AnimalCost", back_populates="animal")

    __table_args__ = (UniqueConstraint('farm_id', 'tag_code', name='_farm_tag_uc'),)

# --- MANEJOS E HISTÓRICO ---

class Weighing(Base):
    __tablename__ = "weighings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    weight = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    method = Column(String, default="balanca") # balanca, estimativa, fita
    operator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    animal = relationship("Animal", back_populates="weighings")

class Medication(Base):
    __tablename__ = "medications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    product_name = Column(String, nullable=False)
    dose = Column(Float)
    unit = Column(String) # ml, dose, mg
    application_date = Column(DateTime, default=datetime.utcnow)
    care_days = Column(Integer, default=0)
    care_end_date = Column(Date) # Calculado: data + care_days
    
    animal = relationship("Animal", back_populates="medications")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    origin_lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"))
    dest_lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"))
    date = Column(DateTime, default=datetime.utcnow)
    reason = Column(String)
    
    animal = relationship("Animal", back_populates="movements")

# --- ESTOQUE E NUTRIÇÃO ---

class StockItem(Base):
    __tablename__ = "stock_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String) # racao, medicamento, suplemento
    unit = Column(String) # kg, l, saco
    quantity = Column(Float, default=0.0)
    min_quantity = Column(Float, default=0.0)
    unit_cost = Column(Float, default=0.0)

class FeedingPlan(Base):
    __tablename__ = "feeding_plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=False)
    stock_item_id = Column(UUID(as_uuid=True), ForeignKey("stock_items.id"))
    quantity_per_animal = Column(Float, nullable=False)
    frequency = Column(String) # diario, semanal

# --- FINANCEIRO ---

class AnimalCost(Base):
    __tablename__ = "animal_costs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    animal_id = Column(UUID(as_uuid=True), ForeignKey("animals.id"), nullable=False)
    category = Column(String) # compra, sanidade, trato, operacional
    value = Column(Float, nullable=False)
    date = Column(Date, default=date.today)
    description = Column(String)
    
    animal = relationship("Animal", back_populates="costs")

class FixedCost(Base):
    __tablename__ = "fixed_costs"
    id