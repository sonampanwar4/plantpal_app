from schemas.ai_bot import UserChatRequestModel
from sqlalchemy.orm import Session
from services.plant_service import get_user_plants_service
from services.ai_bot_service import get_chat_history_service
from services.care_task_service import get_user_all_active_tasks_service
from plant_pal_bot.ai_bot_client import ask_gpt4o
from schemas.ai_bot import AIChatResponse
from logging import getLogger

logger = getLogger(__name__)

class ChatQueryAnalyze:
    def __init__(self,
                 db: Session,
                 user_data: UserChatRequestModel
                 ):
        self.user_data = user_data
        self.db = db

    def build_context(self) -> dict:
        context = {}
        # user's all plants
        plants = get_user_plants_service(db=self.db, user_id=self.user_data.user_id)
        plant_context = [
            f"ID: {p.id}, Name: {p.name}, Species: {p.species}, Location: {p.plant_location}\n"
            for p in plants
        ] if plants else "You have no plants."

        context["plants_owned"] = "".join(plant_context)

        # user's all chat history, min 5
        history = get_chat_history_service(db=self.db, user_id=self.user_data.user_id)[:5]
        history_context = []
        if history:
            for chat in history:
                if chat["is_user"]:
                    history_context.append(f"User: {chat['text']}\n")
                else:
                    history_context.append(f"AI bot: {chat['text'][:200]}\n")

        context["recent_chats"] = "".join(history_context) if history_context else "No previous conversations."

        # user's all active tasks
        active_tasks = get_user_all_active_tasks_service(db=self.db, user_id=self.user_data.user_id)
        task_context = [f"Title: {task.title}, Task type: {task.task_type.value}"
            f"Plant ID: {task.plant_id}, due_date: {task.due_date}, "
            f"description: {task.description[:150] if task.description else 'No plants registered yet.'}\n"
             for task in active_tasks[:5]
        ]

        context["active_care_tasks"] = "".join(task_context) if active_tasks else "No active care tasks."

        return context

    def build_enriched_prompt(self, context: dict) -> str:
        OFF_TOPIC_RESPONSE = """I apologize, but I couldn't answer that question as it's not related to plant care. I'm PlantPal, a specialized assistant dedicated to helping you with plant-related topics only.
        Would you like to ask me anything plant-related? 🌿"""

        return f"""If user concern is not plan-related, respond a request. eg: {OFF_TOPIC_RESPONSE}. Otherwise respond as per following IMPORTANT GUIDELINES.

Current Plants Owned: {context['plants_owned']}
Active Care Tasks:
{context['active_care_tasks']}

Recent Conversation History (last maximum 5 interactions):
{context['recent_chats']}

USER CONCERN: {self.user_data.input_text}

IMPORTANT GUIDELINES:
1. Base your response on the user's current plants, user's recent conversation history and active care tasks
2. Consider the user's recent conversation history for continuity
3. Provide summary of Recent Conversation History, if user concern is related to summarize his history chat with bot
4. If the user has mentioned a specific plant, prioritize advice for that plant
5. Suggest relevant care tasks when appropriate
"""

    async def get_response_from_llm(self):
        context = self.build_context()
        user_prompt = self.build_enriched_prompt(context=context)
        response = await ask_gpt4o(
            user_prompt=user_prompt,
            response_model=AIChatResponse,
            token=200,
            temperature=0.5
        )
        print(response)
        return response.get("ai_response", "")