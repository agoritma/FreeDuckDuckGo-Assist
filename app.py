import asyncio
import aiohttp
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

vqdToken = ""

class DuckDuckAssist():
    def __init__(self) -> None:
        self.STATUS_URL = "https://duckduckgo.com/duckchat/v1/status"
        self.CHAT_URL = "https://duckduckgo.com/duckchat/v1/chat"
        self.BASE_HEADER = {
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/json",
            "Origin": "https://duckduckgo.com",
            "Referer": "https://duckduckgo.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        self.generateDelay = 3600
        
    async def getVQDToken(self) -> None:
        global vqdToken
        getTokenHeader = self.BASE_HEADER
        getTokenHeader["X-Vqd-Accept"] = "1"
        async with aiohttp.ClientSession() as session:
            async with session.get(self.STATUS_URL, headers=getTokenHeader) as response:
                vqdToken = dict(response.headers.items())["x-vqd-4"]
                print("Token has generated: " + vqdToken)
                    
    async def conversation(self, message:list, model:str, stream:bool):
        global vqdToken
        conHeader = self.BASE_HEADER
        conHeader["X-Vqd-4"] = vqdToken
        conHeader["Accept"] = "text/event-stream"
        payload = {
            "model": model,
            "messages": message
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.STATUS_URL, headers=self.BASE_HEADER) as response:
                newHeaders = response.headers
            
            async with session.post(self.CHAT_URL, headers=conHeader, json=payload) as response:
                if (response.status == 200):
                    fullMessage = ""
                    async for chunk in response.content:
                        data_str = chunk.decode("utf-8")
                        json_str = data_str.replace("data: ", "")
                        if json_str == "\n" or json_str.strip() == "[DONE]":
                            pass
                        else:
                            data_dict = json.loads(json_str)
                            try:
                                messChunk = data_dict["message"]
                                fullMessage += messChunk
                                resp = {
                                    "model": data_dict["model"],
                                    "id": data_dict["id"],
                                    "created": data_dict["created"],
                                    "role": "assistant",
                                    "message": fullMessage
                                }
                                if stream:
                                    yield json.dumps(resp).encode("utf-8")
                                    yield "\n".encode()
                            except KeyError:
                                resp = {
                                    "model": data_dict["model"],
                                    "id": data_dict["id"],
                                    "created": data_dict["created"],
                                    "role": "assistant",
                                    "message": fullMessage
                                }
                                if stream:
                                    yield json.dumps(resp).encode("utf-8")
                                    yield "\n".encode()
                    else:
                        if stream:
                            yield '[DONE]'.encode()
                        else:
                            yield json.dumps(resp).encode()
                            yield "\n".encode()
                            yield '[DONE]'.encode()
                else:
                    errRespJson = await response.json()
                    errResp = {
                        "detail": [
                            {
                            "loc": [
                                "request"
                            ],
                                "msg": f"duckduckgo api give status code {errRespJson['status']}",
                                "type": errRespJson["type"]
                            }
                        ]
                    }
                    yield json.dumps(errResp).encode()
                    yield "\n".encode()
                    yield "[DONE]".encode()
    
app = FastAPI()
assist = DuckDuckAssist()

origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    asyncio.create_task(assist.getVQDToken())

@app.get("/")
async def root():
    return {
        "action": "success",
        "status": 200
    }
    
class MessageItems(BaseModel):
    role:str = "user"
    content:str
    
class ConversationItems(BaseModel):
    model:str = "gpt-3.5-turbo-0125"
    messages: List[MessageItems]
    stream:bool = True
    
@app.post("/api/conversation")
async def conversation(payload: ConversationItems):
    if payload.model != "gpt-3.5-turbo-0125":
        raise HTTPException(400, "Model only support 'gpt-3.5-turbo-0125'", headers={"loc": "model", "input": payload.model, "type": "invalid input"})
    
    messageList = [item.model_dump() for item in payload.messages]
    if (messageList[-1]["role"] != "user"):
        raise HTTPException(400, "Role must be 'user'", headers={"loc": "role", "input": messageList[-1]["role"], "type": "invalid input"})
    if (messageList[-1]["content"] == ""):
        raise HTTPException(400, "Content cant be empty", headers={"loc": "content", "input": messageList[-1]["content"], "type": "invalid input"})
    resp = StreamingResponse(assist.conversation(messageList, payload.model, payload.stream), media_type="text/event-stream")
    return resp

@app.exception_handler(HTTPException)
async def httpExceptionHandler(request: Request, exc: HTTPException):
    return JSONResponse (
        status_code= exc.status_code,
        content= {
            "detail": [
                {
                    "type": exc.headers["type"],
                    "loc": [
                        "body",
                        exc.headers["loc"]
                    ],
                    "msg": exc.detail,
                    "input": exc.headers["input"]
                }
            ]
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="localhost", reload=True)