import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from duckassist import DuckDuckAssist
    
app = FastAPI()
assist = DuckDuckAssist()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": 200,
        "how_to_use": "https://github.com/jokosantosi/FreeDuckDuckGo-Assist",
        "example": "https://github.com/jokosantosi/FreeDuckDuckGo-Assist/blob/main/example.py"
    }
    
@app.get("/get-token")
async def getToken():
    try:
        token = await asyncio.create_task(assist.getVQDToken())
        return {
            "status": 200,
            "message": "Success creating a token",
            "token": token
        }
    except:
        return {
            "status": 500,
            "message": "Failed createing a token"
        }
    
@app.post("/api/conversation")
async def conversation(token:str, message:str, stream:bool):
    data = {
            "role": "user",
            "content": message
        }
    resp = StreamingResponse(assist.conversation(token, data, stream=stream), media_type="text/event-stream")
    return resp

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", reload=True)