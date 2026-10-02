import os
import time
from dotenv import load_dotenv

load_dotenv()
from src.app import get_chatbot_runnable

runnable = get_chatbot_runnable("meta-llama/llama-4-maverick-17b-128e-instruct")

messages = []
start = time.time()
print("Invoking chatbot query: 'Explain the Transformer architecture'")
res = runnable.invoke({
    "query": "Explain the Transformer architecture",
    "chat_history": messages,
    "forced_mode": "vectorstore"
})
print("Total invoke time:", time.time() - start)
print("Answer length:", len(res.get("answer", "")))
print("Mode:", res.get("retrieval_mode"))

