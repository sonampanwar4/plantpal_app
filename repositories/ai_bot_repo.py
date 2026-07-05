import uuid
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from models.ai_bot import AILog, AIResponse, ConversationSession
from logging import getLogger

logger = getLogger(__name__)


def create_new_session(db: Session, user_id: int) -> str | None:
    """Create a new conversation session and return session ID."""
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Create new session record
        session = ConversationSession(user_id=user_id, session_id=session_id, is_active=True)
        db.add(session)
        db.commit()
        return session_id
    except Exception as e:
        db.rollback()
        logger.error(f"Error in create_new_session: {str(e)}")


def get_current_session_id(db: Session, user_id: int) -> str:
    """Get the current active session ID for the user."""
    try:
        session = db.query(ConversationSession).filter(ConversationSession.user_id == user_id,
                                                       ConversationSession.is_active == True
                                                       ).order_by(ConversationSession.created_at.desc()).first()
        if session:
            return session.session_id
        else:
            # Create new session if none exists
            return create_new_session(db, user_id)
    except Exception as e:
        logger.error(f"Error in get_current_session_id: {str(e)}")
        # Create new session as fallback
        return create_new_session(db, user_id)

def get_user_last_question(db: Session, user_id: int) -> AILog | None:
    """Get the last question response from the database with session ID."""
    try:
        return (db.query(AILog).filter(AILog.user_id == user_id)
                .order_by(AILog.created_at.desc())).first()
    except Exception as e:
        logger.error(f"Error in get_user_last_question: {str(e)}")
        return None

def get_ai_log_by_user_input_text(db: Session, user_id: int, user_message: str, chat_type: str):
    """Get AI log by photo message for a user if it exists."""
    try:
        return db.query(AILog).filter(AILog.user_id == user_id,
                                      AILog.input_text == user_message,
                                      AILog.chat_type == chat_type).first()
    except Exception as e:
        logger.error(f"Error in get_user_question_by_photo_message: {str(e)}")

def save_chat_message(
        db: Session,
        user_id: int,
        text: str,
        chat_type: str,
        is_user: bool,
        ai_log_id: int = None,
        session_id: str = None):
    """Save an analyse_chat_2 message to the database with session ID."""
    try:
        # Get current session ID if not provided
        if not session_id:
            session_id = get_current_session_id(db, user_id)

        if is_user:
            # Saved a User input text
            # get AI log if user's text is matched in the database
            user_input = get_ai_log_by_user_input_text(db, user_id, text, chat_type)
            # update AI log for session id and date only if user ask same query again
            if user_input:
                user_input.session_id = session_id
                user_input.created_at = datetime.now()
                db.commit()
                return user_input
            else:
                # save new user input
                ai_log = AILog(user_id=user_id, input_text=text, chat_type=chat_type, session_id=session_id,
                               is_permanent=True)
                db.add(ai_log)
                db.commit()
                db.refresh(ai_log)
                return ai_log
        else:
            # Save AI response - find the most recent user input without response
            if ai_log_id:
                latest_input = get_user_last_question(db, user_id)

                if latest_input:
                    ai_response = AIResponse(ai_log_id=latest_input.id, user_id=user_id,
                                             response_text=text, is_permanent=True)
                    db.add(ai_response)
                    db.commit()
                    db.refresh(ai_response)
                    return ai_response
            return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error in save_chat_message: {str(e)}")
        raise


def get_all_chat_history(db: Session, user_id: int) -> list[dict]:
    """Get current session analyse_chat_2 history for display."""
    try:
        # Get current session ID
        session_id = get_current_session_id(db, user_id)

        # Get all AI logs for the current session
        logs = db.query(AILog).filter(AILog.user_id == user_id,
                                      AILog.session_id == session_id, AILog.is_permanent == True
                                      ).order_by(AILog.created_at).all()
        history = []
        # Process each log entry
        for log in logs:
            # Only add user message if there's also an AI response
            ai_response = db.query(AIResponse).filter(AIResponse.ai_log_id == log.id).first()
            if log.input_text and ai_response:
                # Add user message
                history.append({"is_user": True, "text": log.input_text, "created_at": log.created_at})
                # Add AI response
                history.append({"is_user": False, "text": ai_response.response_text,
                                "created_at": ai_response.created_at})
        # Also get standalone AI responses for this session (like welcome messages)
        # We'll need to track welcome messages with session ID too. Get most recent welcome message
        standalone_responses = db.query(AIResponse).filter(AIResponse.user_id == user_id,
                                                           AIResponse.ai_log_id.is_(None),
                                                           AIResponse.is_permanent == True
                                                           ).order_by(AIResponse.created_at.desc()).limit(1).all()

        for response in standalone_responses:
            history.append({"is_user": False, "text": response.response_text, "created_at": response.created_at})

        # Sort by creation time
        history.sort(key=lambda x: x["created_at"])
        for item in history:
            item["timestamp"] = item["created_at"].strftime("%H:%M")  # Add timestamps to the final result
            del item["created_at"]
        return history
    except Exception as e:
        logger.error(f"Error in get_chat_history: {str(e)}")
        return []

def get_complete_conversation_history(db: Session, user_id: int) -> list:
    """Get complete conversation history for AI context (all past conversations)."""
    try:
        # Get all permanent conversations for the user (all sessions)
        logs = db.query(AILog).filter(AILog.user_id == user_id,
                                      AILog.is_permanent == True).order_by(AILog.created_at).all()
        conversation_lines = []
        for log in logs:
            conversation_lines.append(f"User: {log.input_text}")  # Add user message
            ai_response = db.query(AIResponse).filter(AIResponse.ai_log_id == log.id).first()  # Add AI response
            if ai_response:
                conversation_lines.append(f"PlantPal: {ai_response.response_text}")
        #TODO
        # Also get standalone AI responses
        standalone_responses = db.query(AIResponse).filter(AIResponse.user_id == user_id,
                                                           AIResponse.ai_log_id.is_(None),
                                                           AIResponse.is_permanent == True
                                                           ).order_by(AIResponse.created_at).all()
        for response in standalone_responses:
            conversation_lines.append(f"PlantPal: {response.response_text}")

        return conversation_lines
    except Exception as e:
        logger.exception(f"Error in get_complete_conversation_history: {str(e)}")
        return ""

def get_complete_conversation_history_for_a_plant(db: Session, user_id: int, plant_id: int):
    try:
        logs = (
        db.query(
            AILog.id,
            AILog.input_text,
            AILog.created_at,
            AIResponse.response_text
        )
        .join(AIResponse, AIResponse.ai_log_id == AILog.id)
        .filter(AILog.plant_id == plant_id, AILog.user_id == user_id)
        .order_by(AILog.created_at.asc())
        .all()
        )
        return logs
    except Exception as e:
        logger.exception(f"Error in get_complete_conversation_history_for_a_plant: {str(e)}")
        return None


def clear_session(db: Session, user_id: int):
    """Clear current session when user logs out."""
    try:
        # Mark current session as inactive
        session = db.query(ConversationSession).filter(ConversationSession.user_id == user_id,
                                                       ConversationSession.is_active == True).first()
        if session:
            session.is_active = False
            session.ended_at = datetime.now()
            db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error in clear_session: {str(e)}")


def check_duplicate_question(db: Session, user_id: int, user_message: str):
    """Check if user has asked this question before and return duplicate info if found."""
    try:
        # Normalize the user message for comparison (remove extra spaces, convert to lowercase)
        normalized_message = ' '.join(user_message.lower().split())
        # Get all previous user inputs for this user
        previous_inputs = db.query(AILog).filter(
            AILog.user_id == user_id,
            AILog.input_text.isnot(None),
            AILog.is_permanent == True
        ).order_by(AILog.created_at.desc()).all()
        for prev_input in previous_inputs:
            # Normalize previous message for comparison
            normalized_prev = ' '.join(prev_input.input_text.lower().split())
            # Check for exact match or very similar questions (90% similarity threshold)
            if normalized_message == normalized_prev:
                # Exact match found
                return {'ai_log_id': prev_input.id, 'original_question': prev_input.input_text, 'match_type': 'exact'}

            elif len(normalized_message) > 10 and len(normalized_prev) > 10:
                # Check for similarity (simple word overlap for now)
                message_words = set(normalized_message.split())
                prev_words = set(normalized_prev.split())
                if len(message_words) > 0 and len(prev_words) > 0:
                    overlap = len(message_words.intersection(prev_words))
                    total_words = len(message_words.union(prev_words))
                    similarity = overlap / total_words if total_words > 0 else 0
                    if similarity >= 0.8:  # 80% similarity threshold
                        return {'ai_log_id': prev_input.id, 'original_question': prev_input.input_text,
                                'match_type': 'similar', 'similarity': similarity
                                }
        return None  # No duplicate found
    except Exception as e:
        logger.error(f"Error in check_duplicate_question: {str(e)}")
        return None


def update_existing_response(db: Session, user_id: int, ai_log_id: int, new_response: str):
    """Update an existing AI response with a new response."""
    try:
        # Find the existing AI response for this log
        existing_response = db.query(AIResponse).filter(AIResponse.ai_log_id == ai_log_id,
                                                        AIResponse.user_id == user_id).first()
        if existing_response:
            # Update the response text
            existing_response.response_text = new_response
            existing_response.created_at = datetime.now()
            db.commit()
            return existing_response
        else:
            logger.error(f"No existing response found for ai_log_id: {ai_log_id}")
            return existing_response
    except Exception as e:
        db.rollback()
        logger.error(f"Error in update_existing_response: {str(e)}")
        return None
