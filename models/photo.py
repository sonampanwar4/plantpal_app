from sqlalchemy import Column, Integer, String, Text, ForeignKey, CheckConstraint, TIMESTAMP, text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class PlantPhoto(Base):
    """Enhanced plant photo model with diagnosis support."""
    __tablename__ = 'plant_photos'

    id = Column(Integer, primary_key=True, nullable=False)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    image_path = Column(Text, nullable=False, unique=True)
    original_filename = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    diagnosis_status = Column(String(50), nullable=False, default='pending')
    user_query = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    plant = relationship("Plant", back_populates="photos")
    user = relationship("User")
    diagnoses = relationship("PhotoDiagnosis", back_populates="photo", cascade="all, delete")


class PhotoDiagnosis(Base):
    """Store AI diagnosis results for plant photos."""
    __tablename__ = 'photo_diagnoses'

    id = Column(Integer, primary_key=True, nullable=False)
    photo_id = Column(Integer, ForeignKey('plant_photos.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    diagnosis_text = Column(Text, nullable=False)
    confidence_score = Column(Float, CheckConstraint('confidence_score >= 0 AND confidence_score <= 1'))
    identified_issues = Column(JSONB, nullable=True)
    recommended_actions = Column(JSONB, nullable=True)
    treatment_outcome = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    photo = relationship("PlantPhoto", back_populates="diagnoses")
    user = relationship("User")
