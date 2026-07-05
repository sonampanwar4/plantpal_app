from repositories.plant_repo import (
     get_user_plants, get_user_plant, update_user_plant,
    delete_user_plant, find_plant_by_name, create_user_plant
)
from schemas.plant import PlantCreate, PlantUpdate
from sqlalchemy.orm import Session
from models.plant import Plant
from typing import List


def create_user_plant_service(db: Session, plant: PlantCreate, user_id: int):
    """Create a new plant for the specified user."""
    return create_user_plant(db, plant, user_id)


def get_user_plants_service(db: Session, user_id: int) -> List[Plant()] | None:
    """Get all plants belonging to the specified user."""
    return get_user_plants(db, user_id)


def get_plant_service(db: Session, plant_id: int, user_id: int) -> Plant:
    """Get a specific plant by ID for the specified user."""
    return get_user_plant(db, plant_id, user_id)


def update_plant_service(db: Session, plant_id: int, plant_update: PlantUpdate, user_id: int):
    """Update a plant's details for the specified user."""
    return update_user_plant(db, plant_id, plant_update, user_id)


def delete_plant_service(db: Session, plant_id: int, user_id: int):
    """Delete a plant for the specified user."""
    return delete_user_plant(db, plant_id, user_id)

def generate_plant_context_service(db: Session, user_id: int):
    plants = get_user_plants_service(db, user_id)
    plant_context = []
    for plant in plants:
        plant_context.append(f"Plant name: {plant.name}, species: {plant.species}, location: {plant.location}\n")

    return plant_context