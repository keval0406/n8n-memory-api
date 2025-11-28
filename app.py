# import uvicorn
# from fastapi import FastAPI, Body
# from typing import List, Dict, Any
# from fastapi.responses import JSONResponse

# app = FastAPI()

# # Global conversation history
# history = {"history": []}


# @app.get("/")
# async def root():
#     """Return a welcome message."""
#     return {"message": "Welcome to the N8N Agents Memory API Service!"}


# @app.post("/history")
# async def add_to_history(payload: List[Dict[str, Any]] = Body(...)):
#     """
#     Payload format:
#     [
#         { "role": "user", "message": "text" },
#         { "role": "ai", "message": "text" }
#     ]
#     """
#     # Validate array items
#     for item in payload:
#         if "role" not in item or "message" not in item:
#             return {"error": "Each item must contain 'role' and 'message'."}

#         history["history"].append(item)

#     return {
#         "status": "added",
#         "added_messages": len(payload),
#         "total_messages": len(history["history"]),
#         "history": history["history"]
#     }


# @app.get("/history")
# async def get_history():
#     """Return entire stored conversation."""
#     return JSONResponse(content=history)

# @app.delete("/history")
# async def clear_history():
#     """Delete all stored conversation history."""
#     history["history"].clear()
#     return {
#         "status": "cleared",
#         "total_messages": 0,
#         "history": history["history"]
#     }

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=5000)

import os
import json
import redis
import uvicorn
from fastapi import FastAPI, Body
from typing import List, Dict, Any
from fastapi.responses import JSONResponse

app = FastAPI()
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))

r = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

REDIS_KEY = "conversation_history"


@app.get("/")
async def root():
    return {"message": "Welcome to the N8N Agents Memory API Service!"}


@app.get("/get-session-id")
def get_session_id():
    """Generate and return a unique session ID."""
    import uuid
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}


@app.post("/history")
async def add_to_history(payload: List[Dict[str, Any]] = Body(...)):
    """
    Payload format:
    [
        {"role": "user", "message": "text"},
        {"role": "ai", "message": "text"}
    ]
    """

    # Validate array items
    for item in payload:
        if "role" not in item or "message" not in item:
            return {"error": "Each item must contain 'role' and 'message'."}

        # Push each message as JSON string into Redis list
        r.rpush(REDIS_KEY, json.dumps(item))

    total_messages = r.llen(REDIS_KEY)

    return {
        "status": "added",
        "added_messages": len(payload),
        "total_messages": total_messages,
        # "current_history": [json.loads(r.lindex(REDIS_KEY, i)) for i in range(total_messages)]
    }


@app.get("/history")
async def get_history():
    """Return entire stored conversation."""
    raw_items = r.lrange(REDIS_KEY, 0, -1)
    history = [json.loads(item) for item in raw_items]

    return JSONResponse(content={"history": history})


@app.delete("/history")
async def clear_history():
    """Clear the conversation history."""
    r.delete(REDIS_KEY)
    return {"status": "cleared"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
