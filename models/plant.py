from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    TIMESTAMP, Text, text
)
from sqlalchemy.orm import relationship
from database import Base


class Plant(Base):
    """Represents a user's plant and its care details."""
    __tablename__ = 'plants'

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    name = Column(String(100), nullable=False)
    species = Column(String(100), nullable=True)
    home_location = Column(String(100), nullable=False)
    plant_location = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=text('now()'))
    # Relationships
    user = relationship("User", back_populates="plant")
    photos = relationship("PlantPhoto", back_populates="plant", cascade="all, delete")
    ai_logs = relationship("AILog", back_populates="plant", cascade="all, delete")
    care_tasks = relationship("PlantCareTask", back_populates="plant", cascade="all, delete")
