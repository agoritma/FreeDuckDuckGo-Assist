import aiohttp
import json


class DuckDuckAssist:
    def __init__(self) -> None:
        self.STATUS_URL = "https://duckduckgo.com/duckchat/v1/status"
        self.CHAT_URL = "https://duckduckgo.com/duckchat/v1/chat"
        self.BASE_HEADER = {
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/json",
            "Origin": "https://duckduckgo.com",
            "Referer": "https://duckduckgo.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }

    async def getVQDToken(self) -> None:
        header = self.BASE_HEADER
        header["X-Vqd-Accept"] = "1"
        async with aiohttp.ClientSession() as session:
            async with session.get(self.STATUS_URL, headers=header) as response:
                if response.status == 200:
                    vqdToken = dict(response.headers.items())["x-vqd-4"]
                    return vqdToken
                else:
                    raise Exception("Failed to get token")

    async def completionsStream(self, token: str, message: list, model: str):
        completionsHeader = self.BASE_HEADER
        completionsHeader["X-Vqd-4"] = token
        completionsHeader["Accept"] = "text/event-stream"

        payload = {"model": model, "messages": message}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.CHAT_URL, headers=completionsHeader, json=payload
            ) as response:
                if response.status != 200:
                    errRespJson = await response.json()
                    yield f"duckduckgo api give status code {errRespJson['status']}, {errRespJson['type']}"
                    return
                responseVQD = dict(response.headers.items())["x-vqd-4"]
                async for chunk in response.content:
                    data_str = chunk.decode("utf-8")
                    json_str = data_str.replace("data: ", "")
                    if json_str == "\n" or json_str.strip() == "[DONE]":
                        continue
                    data_dict = json.loads(json_str)
                    try:
                        messChunk = data_dict["message"]
                        resp = {
                            "id": data_dict["id"],
                            "object": "chat.completion",
                            "created": data_dict["created"],
                            "model": model,
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                                "total_tokens": 0,
                                "completion_token_details": {
                                    "reasoning_tokens": 0,
                                    "accepted_prediction_tokens": 0,
                                    "rejected_prediction_tokens": 0,
                                },
                            },
                            "choice": [
                                {
                                    "message": {
                                        "role": "assistant",
                                        "content": messChunk,
                                    },
                                    "logprobs": None,
                                    "finish_reason": None,
                                    "index": 0,
                                }
                            ],
                            "next_vqd_token": responseVQD,
                        }
                        yield f"{json.dumps(resp)}\n".encode("utf-8")
                    except KeyError:
                        pass

    async def completions(self, token: str, message: list, model: str):
        conHeader = self.BASE_HEADER
        conHeader["X-Vqd-4"] = token
        conHeader["Accept"] = "text/event-stream"

        payload = {"model": model, "messages": message}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.CHAT_URL, headers=conHeader, json=payload
            ) as response:
                if response.status != 200:
                    errRespJson = await response.json()
                    yield f"duckduckgo api give status code {errRespJson['status']}, {errRespJson['type']}"
                    return
                responseVQD = dict(response.headers.items())["x-vqd-4"]
                fullMessage = ""
                async for chunk in response.content:
                    data_str = chunk.decode("utf-8")
                    json_str = data_str.replace("data: ", "")
                    if json_str == "\n" or json_str.strip() == "[DONE]":
                        continue
                    data_dict = json.loads(json_str)
                    try:
                        fullMessage += data_dict["message"]
                    except KeyError:
                        pass
                resp = {
                    "id": data_dict["id"],
                    "object": "chat.completion",
                    "created": data_dict["created"],
                    "model": model,
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "completion_token_details": {
                            "reasoning_tokens": 0,
                            "accepted_prediction_tokens": 0,
                            "rejected_prediction_tokens": 0,
                        },
                    },
                    "choice": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": fullMessage,
                            },
                            "logprobs": None,
                            "finish_reason": "stop",
                            "index": 0,
                        }
                    ],
                    "next_vqd_token": responseVQD,
                }
                yield json.dumps(resp)
