import requests

API_URL = "http://localhost:8000"
API_KEY = "k1n0V3rs3-Pr0d-2025-S3cr3t"
HEADERS = {"X-API-KEY": API_KEY}

def create_session(starting_message: str) -> str:
    url = f"{API_URL}/chat/sessions"
    params = {"starting_message": starting_message}
    response = requests.post(url, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    print(f"Session created: {data['session_id']}")
    return data["session_id"]

def send_message(session_id: str, message: str) -> str:
    url = f"{API_URL}/chat/sessions/{session_id}/messages"
    params = {"message": message}
    response = requests.post(url, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    print(f"Assistant: {data['response']}")
    return data["response"]

def delete_session(session_id: str):
    url = f"{API_URL}/chat/sessions/{session_id}"
    response = requests.delete(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    print(f"Deleted session: {data['session_id']}")

if __name__ == "__main__":

    follow_up = "Ozbek tilini bilasan-a? oxirgi postimni ozbek tilida qayta yozhchi tushunmadim"
    assistant_reply = send_message("540223d4-ae00-46e1-a8aa-817039d1ab2d", follow_up)


