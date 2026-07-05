from utils.helper import fix_numbered_lists
from services.ai_bot_service import (
    save_bot_message_service, save_user_message_service
)
from schemas.ai_bot import UserChatRequestModel
from sqlalchemy.orm import Session

from plant_pal_bot.analyze_chat import ChatQueryAnalyze
from services.photo_service import (
    save_user_photo_on_local_service,
    get_user_image_by_file_path_service,
)
from plant_pal_bot.analyze_photo import PlantPhotoAnalyze
from utils.image_processor import validate_image_exists
from logging import getLogger

logger = getLogger(__name__)


def save_chat_messages_service(db: Session, user_data: UserChatRequestModel, ai_response: str) -> bool:
    """Centralized message saving with transaction safety, save data only if plant related query"""
    ai_log = save_user_message_service(db=db,
                                       user_id=user_data.user_id,
                                       message=user_data.input_text,
                                       chat_type=user_data.chat_type)

    if ai_log:
        # Save bot response
        saved_response = save_bot_message_service(
            db=db,
            user_id=user_data.user_id,
            ai_log_id=ai_log.id,
            message=ai_response,
            chat_type=user_data.chat_type)

        if saved_response:
            return True

    return False

async def analyze_photo_query_service(db: Session, user_data: UserChatRequestModel) -> str | None:
    # ========== Step 1: Fetch Photo Data ==========
    photo_path = ""
    photo_id = None
    local_photo = None
    if isinstance(user_data.photo_file, str):
        if validate_image_exists(user_data.photo_file):
            photo = get_user_image_by_file_path_service(db=db,
                                                        user_id=user_data.user_id,
                                                        photo_path=user_data.photo_file)
            photo_path = photo.image_path
            photo_id = photo.id

    if not photo_path and not photo_id:
        photo = await save_user_photo_on_local_service(db=db, file=user_data.photo_file, user_id=user_data.user_id)
        photo_path = photo.image_path
        local_photo = photo

    analyzer = PlantPhotoAnalyze(
        db=db,
        user_id=user_data.user_id,
        plant_id=user_data.plant_id,
        photo_id=photo_id,
        user_query=user_data.input_text,
        image_path=photo_path,
        local_photo_detail= local_photo
    )

    # Vision analysis generates diagnosis - Deeper LLM analysis
    ai_response = await analyzer.get_llm_response()
    return ai_response



async def analyze_chat_query_service(db: Session, user_data: UserChatRequestModel) -> str | None:
    chat = ChatQueryAnalyze(db=db, user_data=user_data)
    ai_response = await chat.get_response_from_llm()
    return ai_response


async def handle_ai_chat_service(db: Session, user_data: UserChatRequestModel) -> str:
    """Handle AI analyse_chat_2 interaction using chain of responsibility pattern."""
    try:
        if user_data.plant_id and user_data.photo_file:
            ai_response = await analyze_photo_query_service(db, user_data)
        else:
            ai_response = await analyze_chat_query_service(db, user_data)

        if ai_response:
            success = save_chat_messages_service(db=db, user_data=user_data, ai_response=ai_response)
            if success:
                bot_response = fix_numbered_lists(ai_response)
                return bot_response
        raise Exception("Failed saving data")
    except Exception as e:
        logger.exception(f"❌ Failed handling AI response: {str(e)}")
        return "I'm sorry, I'm having trouble processing your request right now. Please try again in a moment."