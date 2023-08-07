import os

import torch
import transformers
from beam import App, Runtime, Image, Volume
from langchain import HuggingFacePipeline
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from torch import bfloat16
from transformers import StoppingCriteria, StoppingCriteriaList, BitsAndBytesConfig, AutoConfig, AutoTokenizer, \
    AutoModelForCausalLM

HF_CACHE = "./models"
MODEL_ID = 'meta-llama/Llama-2-7b-chat-hf'
APP_NAME = "travel-guru"
GPU = "T4"
MEMORY = "2Gi"

app = App(name=APP_NAME,
          volumes=[
              Volume(
                  name="my_models",
                  path=HF_CACHE,
              )
          ],
          runtime=Runtime(gpu=GPU,
                          memory=MEMORY,
                          image=Image(python_packages="requirements.txt")))


@app.rest_api()
def chat(**inputs):
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type='nf4',
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=bfloat16
    )

    model_config = AutoConfig.from_pretrained(
        MODEL_ID,
        use_auth_token=os.getenv("HF_TOKEN"),
        cache_dir=HF_CACHE
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        trust_remote_code=True,
        config=model_config,
        quantization_config=bnb_config,
        device_map='auto',
        use_auth_token=os.getenv("HF_TOKEN"),
        cache_dir=HF_CACHE
    )

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        use_auth_token=os.getenv("HF_TOKEN"),
        cache_dir=HF_CACHE,
    )

    model.eval()

    class StopOnTokens(StoppingCriteria):
        def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
            for stop_ids in stop_token_ids:
                if torch.eq(input_ids[0][-len(stop_ids):], stop_ids).all():
                    return True
            return False

    stop_list = ["\nhuman:", "\n```\n"]
    stopping_criteria = StoppingCriteriaList([StopOnTokens()])

    stop_token_ids = [tokenizer(x, return_tensors='pt')['input_ids'].squeeze() for x in stop_list]
    stop_token_ids = [torch.LongTensor(x).to("cuda") for x in stop_token_ids]

    pipeline = transformers.pipeline(
        model=model,
        tokenizer=tokenizer,
        return_full_text=True,
        task='text-generation',
        stopping_criteria=stopping_criteria,
        temperature=0.1,
        max_new_tokens=1024,
        repetition_penalty=1.1
    )

    llm = HuggingFacePipeline(pipeline=pipeline)

    prompt = ChatPromptTemplate.from_role_strings([("system", inputs.get("system"))] + [(role, msg) for msg, role in
                                                                                        zip(inputs.get("messages"),
                                                                                            ["human", "ai"] * len(
                                                                                                inputs.get(
                                                                                                    "messages")))] +
                                                  [("ai", "")])

    llm_chain = LLMChain(prompt=prompt, llm=llm)

    res = llm_chain({**inputs, **{"stop": stop_list}})
    return {"message": res}
