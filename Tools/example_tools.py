from langchain_core.tools import tool
from datetime import datetime


@tool
def add_fn(x: str) -> str:
    """
    Add the two numbers given as a single string input, e.g., '35 90'

    Args:
        x: String containing two numbers separated by space

    Returns:
        The sum of the two numbers as a string
    """
    try:
        a, b = map(int, x.strip().split())
        return str(a + b)
    except (ValueError, TypeError) as e:
        return f"Error: Invalid input format. Please provide two numbers separated by space. {e}"


@tool
def subtract_fn(x: str) -> str:
    """
    Subtract the two numbers given as a single string input, e.g., '35 90'

    Args:
        x: String containing two numbers separated by space

    Returns:
        The subtraction result of the two numbers as a string
    """
    try:
        a, b = map(int, x.strip().split())
        return str(a - b)
    except (ValueError, TypeError) as e:
        return f"Error: Invalid input format. Please provide two numbers separated by space. {e}"


@tool
def multiply_fn(x: str) -> str:
    """
    Multiply the two numbers given as a single string input, e.g., '35 90'

    Args:
        x: String containing two numbers separated by space

    Returns:
        The multiplication result of the two numbers as a string
    """
    try:
        a, b = map(int, x.strip().split())
        return str(a * b)
    except (ValueError, TypeError) as e:
        return f"Error: Invalid input format. Please provide two numbers separated by space. {e}"


@tool
def divide_fn(x: str) -> str:
    """
    Divide the two numbers given as a single string input, e.g., '35 5'

    Args:
        x: String containing two numbers separated by space

    Returns:
        The division result of the two numbers as a string
    """
    try:
        a, b = map(float, x.strip().split())
        if b == 0:
            return "Error: Division by zero is not allowed"
        return str(a / b)
    except (ValueError, TypeError) as e:
        return f"Error: Invalid input format. Please provide two numbers separated by space. {e}"


@tool
def get_current_datetime() -> str:
    """
    Gets the current date and time

    Returns:
        Current date and time formatted as string
    """
    try:
        now = datetime.now()
        return f"Current Date and Time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return f"Error getting current time: {e}"


# Create tools list with decorated functions
tools = [
    add_fn,
    subtract_fn,
    multiply_fn,
    divide_fn,
    get_current_datetime
]

