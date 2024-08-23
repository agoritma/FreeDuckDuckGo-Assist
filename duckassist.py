import aiohttp
import json

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
        
    async def getVQDToken(self) -> None:
        getTokenHeader = self.BASE_HEADER
        getTokenHeader["X-Vqd-Accept"] = "1"
        async with aiohttp.ClientSession() as session:
            async with session.get(self.STATUS_URL, headers=getTokenHeader) as response:
                vqdToken = dict(response.headers.items())["x-vqd-4"]
                return vqdToken
                    
    async def conversation(self, token:str, message:list, stream:bool):
        conHeader = self.BASE_HEADER
        conHeader["X-Vqd-4"] = token
        conHeader["Accept"] = "text/event-stream"
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": message
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.STATUS_URL, headers=self.BASE_HEADER) as response:
                pass
            
            async with session.post(self.CHAT_URL, headers=conHeader, json=payload) as response:
                if (response.status == 200):
                    async for chunk in response.content:
                        data_str = chunk.decode("utf-8")
                        json_str = data_str.replace("data: ", "")
                        if json_str == "\n" or json_str.strip() == "[DONE]":
                            pass
                        else:
                            data_dict = json.loads(json_str)
                            try:
                                messChunk = data_dict["message"]
                                resp = {
                                    "model": data_dict["model"],
                                    "id": data_dict["id"],
                                    "created": data_dict["created"],
                                    "role": "assistant",
                                    "message": messChunk,
                                    "resp_token": dict(response.headers.items())["x-vqd-4"]
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
                                    "message": messChunk,
                                    "resp_token": dict(response.headers.items())["x-vqd-4"]
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
