from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse, JSONResponse
from repositories.plant_repo import get_user_plants
from services.user_service import get_current_user_service
from database import get_db
from sqlalchemy.orm import Session
from services.ai_bot_service import (
    get_chat_history_service
)
from services.chat_handler_service import handle_ai_chat_service
from utils.markdown_converter import markdown_to_html
from schemas.user import ResponseUser
from datetime import datetime
from forms.chat_form import ChatForm
from schemas.ai_bot import UserChatRequestModel
from logging import getLogger

logger = getLogger(__name__)


router = APIRouter()
templates = Jinja2Templates(directory="templates")



@router.get("/ai_chat", response_class=HTMLResponse)
async def ai_chat_page(
        request: Request,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user_service)
):
    """Render the AI analyse_chat_2 page with conversation history and user plants."""
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    plants = get_user_plants(db, user.id)
    chat_history = get_chat_history_service(db, user.id)

    # If no chat history exists, show welcome message
    if not chat_history:
        chat_history = [{
            "is_user": False,
            "text": f"Hello **{user.full_name}!** How can I help you today? 🌿",
            "timestamp": datetime.now().strftime("%H:%M")
        }]
    else:
        # Add timestamps to messages if not already present
        for message in chat_history:
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().strftime("%H:%M")

    # Convert markdown to HTML for bot messages
    for message in chat_history:
        if not message["is_user"]:
            message["text"] = markdown_to_html(message["text"])

    response = templates.TemplateResponse("ai_bot_chat.html", {
        "request": request,
        "chat_history": chat_history,
        "user_plants": plants,
        "user": user
    })

    return response


@router.post("/ai_chat", response_class=HTMLResponse)
async def ai_chat(
        request: Request,
        user: ResponseUser = Depends(get_current_user_service),
        db: Session = Depends(get_db),
        chat_form: ChatForm = Depends()
):
    """Handle AI analyse_chat_2 message submission with optional photo upload."""
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    if chat_form.plant_id and chat_form.photo_file:
        chat_type = 'diagnosis'
    else:
        chat_type = 'chat'

    user_data = UserChatRequestModel(
        user_id=user.id,
        input_text=chat_form.user_message,
        plant_id=chat_form.plant_id,
        chat_type = chat_type,
        photo_file=chat_form.photo_file
    )

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        # Handle text-only message or photo + message
        #bot_response = await handle_ai_chat_service(db, user_data)
        bot_response = await handle_ai_chat_service(db, user_data)

        # Convert markdown to HTML for the response
        bot_response_html = markdown_to_html(bot_response)

        if is_ajax:
            return JSONResponse({
                "success": True,
                "bot_response": bot_response_html,
                "user_message": user_data.input_text,
                "timestamp": datetime.now().strftime("%H:%M")
            })
    except Exception as e:
        logger.error(f"Error in ai_chat_post: {str(e)}")
        # If AJAX request, return error JSON
        if is_ajax:
            return JSONResponse({
                "success": False,
                "error": f"Sorry, I encountered an error processing your request: {str(e)}",
                "timestamp": datetime.now().strftime("%H:%M")
            }, status_code=500)
    return RedirectResponse(url="/ai_chat", status_code=status.HTTP_303_SEE_OTHER)
