import aiohttp
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000/api"
TOKEN_URL = BASE_URL+"/get-token"
CHAT_URL = BASE_URL+"/conversation"

token = ""
messHistory:list = []
async def chat(messList):
    global token
    async with aiohttp.ClientSession() as session:
        if (token == ""): #request token if token is empty
            async with session.get(TOKEN_URL) as resp:
                data = await resp.json()
                token = data["token"]

        body= {
            "token": token,
            "message": messList,
            "stream": True
        }
        async with session.post(CHAT_URL, json=body) as resp:
            if resp.status != 200: print("eror")
            fullmessage = ""
            async for chunk in resp.content:
                data_str = chunk.decode("utf-8")
                json_str = data_str.replace("data: ", "")
                if json_str.strip() == "[DONE]":
                    break
                else:
                    try:
                        data_dict = json.loads(json_str)
                        fullmessage += data_dict["message"]
                        token = data_dict["resp_token"] # update token
                    except KeyError:
                        pass
            messHistory.append({"role": "assistant", "content": fullmessage}) #append assistant response to message history
            print("\n", fullmessage, "\n\n")

while True:
    mess = input(">>> ")
    messHistory.append({"role": "user", "content": mess}) #append user message to message history
    asyncio.run(chat(messHistory))