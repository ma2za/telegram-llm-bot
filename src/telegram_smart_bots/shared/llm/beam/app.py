import os

import transformers
from beam import App, Runtime, Image, Volume
from torch import bfloat16
from transformers import (
    BitsAndBytesConfig,
    AutoConfig,
    AutoTokenizer,
    AutoModelForCausalLM,
    Conversation,
)

HF_CACHE = "./models"
MODEL_ID = "meta-llama/Llama-2-7b-chat-hf"
APP_NAME = "travel-guru"
GPU = "T4"
MEMORY = "16Gi"

app = App(
    name=APP_NAME,
    volumes=[
        Volume(
            name="my_models",
            path=HF_CACHE,
        )
    ],
    runtime=Runtime(
        gpu=GPU, cpu=4, memory=MEMORY, image=Image(python_packages="requirements.txt")
    ),
)


@app.rest_api(keep_warm_seconds=100)
def chat(**inputs):
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=bfloat16,
    )

    model_config = AutoConfig.from_pretrained(
        MODEL_ID, use_auth_token=os.getenv("HF_TOKEN"), cache_dir=HF_CACHE
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        trust_remote_code=True,
        config=model_config,
        quantization_config=bnb_config,
        device_map="auto",
        use_auth_token=os.getenv("HF_TOKEN"),
        cache_dir=HF_CACHE,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        use_auth_token=os.getenv("HF_TOKEN"),
        cache_dir=HF_CACHE,
        use_default_system_prompt=False,
    )

    model.eval()

    pipeline = transformers.pipeline(
        model=model,
        tokenizer=tokenizer,
        task="conversational",
        temperature=0.0,
        max_length=1000,
        repetition_penalty=1.1,
    )

    messages = inputs.get("messages")
    past_user_inputs = [m.get("data").get("content") for m in messages[:-1:2]]
    generated_responses = [m.get("data").get("content") for m in messages[1:-1:2]]
    text = messages[-1].get("data").get("content")

    conv = Conversation(
        text, past_user_inputs=past_user_inputs, generated_responses=generated_responses
    )

    out = pipeline(conv)
    return {"message": out.generated_responses[-1]}
