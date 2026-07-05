from repositories.ai_bot_repo import (
    save_chat_message, get_all_chat_history,
    clear_session, get_user_last_question, check_duplicate_question,
    update_existing_response, get_complete_conversation_history,
    get_complete_conversation_history_for_a_plant
)
from repositories.care_task_repo import get_user_care_tasks_for_plant
from logging import getLogger

logger = getLogger(__name__)


# save conversation data
def save_user_message_service(db, user_id, message, chat_type):
    """Save a user message to the analyse_chat_2 history."""
    return save_chat_message(db, user_id=user_id,
                             text=message,
                             is_user=True,
                             chat_type=chat_type)


def save_bot_message_service(db, user_id, ai_log_id, message, chat_type):
    """Save a bot message to the analyse_chat_2 history."""
    return save_chat_message(db, user_id=user_id,
                      text=message,
                      ai_log_id=ai_log_id,
                      is_user=False,
                      chat_type=chat_type)


def get_user_care_tasks_for_plant_service(db, plant_id, user_id):
    """Get user care tasks for a plant."""
    return get_user_care_tasks_for_plant(db, plant_id, user_id)


def get_chat_history_service(db, user_id: int) -> list:
    """Get the analyse_chat_2 history for the specified user."""
    return get_all_chat_history(db, user_id)


def clear_user_session_service(db, user_id: int):
    """Clear user session when logging out."""
    clear_session(db, user_id)


def get_last_question_response_service(db, user_id: int) -> str:
    """Get the user's last question and provide a response."""
    try:
        last_question = get_user_last_question(db, user_id)
        if not last_question:
            return "🌱 You haven't asked any questions yet! This is our first conversation. Feel free to ask me anything about your plants and gardening! 🌿"

        return f"🌱 Your last question was: **\"{last_question}\"** 🌿\n\nWould you like me to answer it again or do you have a new question?"
    except Exception as e:
        logger.exception(f"❌ Error getting last question: {str(e)}")
        return "🌱 I'm having trouble retrieving your last question right now. Please ask me something new! 🌿"


def update_existing_ai_response_service(db, user_id, ai_log_id, ai_response, chat_type:str):
    """Update existing response service."""
    updated_response = update_existing_response(db, user_id, ai_log_id, ai_response)
    if not updated_response:
        updated_response = save_bot_message_service(db=db, user_id=user_id,
                                                    ai_log_id=ai_log_id, message=ai_response,
                                                    chat_type=chat_type)
    return updated_response


def get_complete_conversation_history_service(db, user_id):
    """Get the user's complete conversation history."""
    responses = get_complete_conversation_history(db, user_id)

    return "\n-".join(responses)


def check_duplicate_question_service(db, user_id, user_message):
    """Check if a question already exists."""
    return check_duplicate_question(db, user_id, user_message)

def get_complete_conversation_history_for_a_plant_service(db, user_id, plant_id):
    """Get the user's complete conversation history."""
    return get_complete_conversation_history_for_a_plant(db=db, user_id=user_id, plant_id=plant_id)

#TODO: future task
# def get_user_conversation_detail_for_plant_service(db, plant_id: int, user_id: int):
#     plant = get_plant_service(db, plant_id=plant_id, user_id=user_id)
#     user_logs_for_a_plant = get_complete_conversation_history_for_a_plant_service(
#         db=db,
#         plant_id=plant_id,
#         user_id=user_id)
    # Group by date
    # conversations_by_date = defaultdict(list)
    #
    # for log in user_logs_for_a_plant:
    #     # Convert date → string, e.g. "Jan 1, 2025"
    #     date_string = log.created_at.strftime("%b %d, %Y")
    #     conversations_by_date[date_string].append({
    #         "user_message": log.input_text,
    #         "ai_response": log.response_text,
    #     })
    #TODO: debug
    # print(conversations_by_date)
    # conversations_by_date = {
    #   "Jan 01, 2025": [
    #     {
    #       "user_message": "Why are the leaves yellow?",
    #       "ai_response": "It might be overwatering...",
    #       "time": "14:22"
    #     },
    #     {
    #       "user_message": "Should I move it outside?",
    #       "ai_response": "Yes, more sunlight will help.",
    #       "time": "14:30"
    #     }
    #   ],
    #   "Jan 04, 2025": [
    #     {
    #       "user_message": "It still looks unhealthy",
    #       "ai_response": "Send me a photo so I can diagnose.",
    #       "time": "10:45"
    #     }
    #   ]
    # }
    # return {
    #     "plant": plant,
    #     "chat_history": conversations_by_date
    # }