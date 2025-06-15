import os
from langsmith import Client
from dotenv import load_dotenv

load_dotenv()

def setup_langsmith():
    """Configure LangSmith for monitoring and evaluation"""

    # Set environment variables for LangSmith
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "faq-bot")

    # Initialize LangSmith client
    client = Client()

    return client

def log_feedback(run_id: str, feedback_score: float, feedback_comment: str = ""):
    """Log feedback for a specific run"""
    client = Client()

    try:
        client.create_feedback(
            run_id=run_id,
            key="user_feedback",
            score=feedback_score,
            comment=feedback_comment
        )
        return True
    except Exception as e:
        print(f"Error logging feedback: {e}")
        return False

def create_dataset(dataset_name: str, description: str = ""):
    """Create a dataset for evaluation"""
    client = Client()

    try:
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description=description
        )
        return dataset
    except Exception as e:
        print(f"Error creating dataset: {e}")
        return None