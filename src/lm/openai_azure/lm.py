import logging
import os

import openai
from dotenv import load_dotenv

logging.basicConfig(filename='bot.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

openai.api_type = os.getenv("API_TYPE")
openai.api_base = os.getenv("API_BASE")
openai.api_version = os.getenv("API_VERSION")
openai.api_key = os.getenv("API_KEY")


def chat(**inputs):
    response = openai.ChatCompletion.create(
        engine="telegram",
        messages=[{"role": "system",
                   "content": inputs.get("system")}] + [{"role": role, "content": msg} for msg, role in
                                                        zip(inputs.get("messages"),
                                                            ["user", "assistant"] * len(
                                                                inputs.get(
                                                                    "messages")))],
        temperature=0.7,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)
    return {"message": response.get("choices")[0].get("message").to_dict().get("content")}
