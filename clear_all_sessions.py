import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")

HISTORY_URL = f"{BASE_URL}/history"
RESET_URL = f"{BASE_URL}/history"

TIMEOUT = 5


def fetch_data(session: requests.Session, url: str) -> dict:
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def reset_session(session: requests.Session, session_id: str) -> None:
    response = session.delete(
        RESET_URL,
        params={"sessionId": session_id},
        timeout=TIMEOUT
    )
    response.raise_for_status()
    print(f"Session {session_id} reset successfully.")


def main():
    with requests.Session() as session:
        # Fetch conversation history
        data = fetch_data(session, HISTORY_URL)
        print("Data fetched successfully.")

        conversation_ids = data.get("conversations", {}).keys()

        for session_id in conversation_ids:
            try:
                reset_session(session, session_id)
            except requests.RequestException as e:
                print(f"Error resetting session {session_id}: {e}")

        print("All sessions processed.")

        # Fetch history again to confirm
        fetch_data(session, HISTORY_URL)
        print("Data fetched successfully.")


if __name__ == "__main__":
    main()
