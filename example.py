import aiohttp
import asyncio
import json

body = {
    "model": "gpt-3.5-turbo-0125",
    "messages": [],
    "stream": True
}

async def chat(data):
    async with aiohttp.ClientSession() as session:
        fullmessage = ""
        async with session.post("http://192.168.1.10:8000/api/conversation", json=data) as resp:
            async for chunk in resp.content:
                data_str = chunk.decode("utf-8")
                json_str = data_str.replace("data: ", "")
                if json_str == "\n" or json_str.strip() == "[DONE]":
                    pass
                else:
                    try:
                        data_dict = json.loads(json_str)
                        fullmessage = data_dict["message"]
                    except KeyError:
                        pass
            body["messages"].append({"role": "assistant", "content": fullmessage}) #append assistant response for best result
            print(fullmessage)

while True:
    mess = input(">>> ")
    messages = body["messages"]
    messages.append({"role": "user", "content": mess})
    body["messages"] = messages
    asyncio.run(chat(body))