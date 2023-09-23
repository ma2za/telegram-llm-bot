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
from transformers.models.llama.tokenization_llama_fast import B_SYS, E_SYS

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


def load_model():
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
        temperature=0.1,
        max_length=4096,
        repetition_penalty=1.1,
    )
    return pipeline


@app.rest_api(keep_warm_seconds=100, loader=load_model)
def chat(**inputs):
    pipeline = inputs["context"]
    messages = inputs.get("messages")

    past_user_inputs = [m.get("data").get("content") for m in messages[1:-1:2]]
    generated_responses = [m.get("data").get("content") for m in messages[2:-1:2]]
    text = messages[-1].get("data").get("content")

    conversation = Conversation(
        text, past_user_inputs=past_user_inputs, generated_responses=generated_responses
    )

    system_prompt = f"{B_SYS}{messages[-1].get('data').get('content')}{E_SYS}"

    if len(conversation.past_user_inputs) > 0:
        conversation.past_user_inputs[
            0
        ] = f"{system_prompt}{conversation.past_user_inputs[0]}"
    elif conversation.new_user_input:
        conversation.new_user_input = f"{system_prompt}{conversation.new_user_input}"

    out = pipeline(conversation)
    return {"message": out.generated_responses[-1]}
