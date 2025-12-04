import os
import json
import redis
import uvicorn
from fastapi import FastAPI, Body, Query
from typing import List, Dict, Any
from fastapi.responses import JSONResponse

app = FastAPI()

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))

r = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)


def redis_key(session_id: str) -> str:
    return f"conversation:{session_id}"


@app.get("/")
async def root():
    return {"message": "Welcome to the Multi-Session Memory API!"}


@app.get("/get-session-id")
def get_session_id():
    """Generate and return a unique session ID."""
    import uuid
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}


@app.post("/history")
async def add_to_history(
    session_id: str = Query(..., description="Unique conversation ID"),
    payload: List[Dict[str, Any]] = Body(...)
):
    """
    Payload format:
    [
        {"role": "user", "message": "text"},
        {"role": "ai", "message": "text"}
    ]
    """

    print(session_id)

    key = redis_key(session_id)

    # Validate items
    for item in payload:
        if "role" not in item or "message" not in item:
            return {"error": "Each item must contain 'role' and 'message'."}

        r.rpush(key, json.dumps(item))

    return {
        "status": "added",
        "session_id": session_id,
        "added_messages": len(payload),
        "total_messages": r.llen(key)
    }


# @app.get("/history")
# async def get_history(
#     session_id: str = Query(...),
#     items: int = 10
# ):
#     """Return last `items` messages from the conversation."""
#     key = redis_key(session_id)

#     raw_items = r.lrange(key, 0, -1)
#     history = [json.loads(item) for item in raw_items]

#     return JSONResponse(content={
#         "session_id": session_id,
#         "history": history[-items:]
#     })

@app.get("/history")
async def get_history(
    session_id: str | None = Query(None),
    items: int = 10
):
    """
    If session_id is provided -> return history for that session.
    If session_id is NOT provided -> return all conversations.
    """

    # ---------------------------------------------------------------------
    # CASE 1: session_id given -> fetch specific conversation
    # ---------------------------------------------------------------------
    if session_id:
        key = redis_key(session_id)
        raw_items = r.lrange(key, 0, -1)
        history = [json.loads(item) for item in raw_items]

        return JSONResponse(content={
            "session_id": session_id,
            "history": history[-items:]
        })

    # ---------------------------------------------------------------------
    # CASE 2: No session_id -> return ALL available conversations
    # ---------------------------------------------------------------------

    # List all keys like conversation:*
    all_keys = r.keys("conversation:*")

    all_conversations = {}

    for key in all_keys:
        raw_messages = r.lrange(key, 0, -1)
        history = [json.loads(item) for item in raw_messages]

        # Extract session ID from key
        sid = key.replace("conversation:", "")

        all_conversations[sid] = history if items == -1 else history[-items:]

    return JSONResponse(content={
        "total_conversations": len(all_conversations),
        "conversations": all_conversations
    })


@app.delete("/history")
async def clear_history(session_id: str = Query(...)):
    """Clear a specific conversation."""
    key = redis_key(session_id)
    r.delete(key)
    return {"status": "session cleared", "session_id": session_id}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
