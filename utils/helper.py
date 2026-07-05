from passlib.context import CryptContext
import re
from models.ai_bot import AILog
from fastapi import status
from fastapi.responses import RedirectResponse

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def fix_numbered_lists(text: str) -> str:
    """Fix numbered lists to ensure proper sequential numbering (1, 2, 3, 4, 5...)."""
    lines = text.split('\n')
    fixed_lines = []
    list_counter = 1
    in_list = False

    for line in lines:
        stripped_line = line.strip()

        # Check if line starts with a number followed by a period and space
        if re.match(r'^\d+\.\s', stripped_line):
            # Extract content after the number and period
            content = re.sub(r'^\d+\.\s*', '', stripped_line)
            # Replace with correct sequential number
            fixed_line = f'{list_counter}. {content}'
            fixed_lines.append(fixed_line)
            list_counter += 1
            in_list = True
        else:
            # If we were in a list, and now we're not, reset counter
            if in_list and stripped_line and not stripped_line.startswith('•') and not stripped_line.startswith('-'):
                list_counter = 1
                in_list = False
            fixed_lines.append(line)

    result = '\n'.join(fixed_lines)
    return result


# NEW: Helper function to create mock AILog
def create_mock_ai_log(response_text: str) -> AILog:
    """Create a mock AILog object for responses."""

    class MockAILog:
        def __init__(self, response):
            self.ai_response = response

    return MockAILog(response_text)

def redirect_with_message(
    url: str,
    message: str,
    message_type: str = "success",
    status_code: int = status.HTTP_200_OK,
):
    response = RedirectResponse(url=url, status_code=status_code)
    response.set_cookie("message", message, max_age=5, path="/")
    response.set_cookie("message_type", message_type, max_age=5, path="/")
    return response