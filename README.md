# Telegram LLM Bot

This is a guide on how to build a Telegram Bot backed by
an LLM (i.e. llama2-chat, llama2-chat-32k, vicuna). The bot is
hosted on a free tier EC2 instance, the llm inference is hosted on
Beam Cloud as a serverless REST API, which is free for the first
10 hours of compute. The whole thing is quite slow, but this is just
a starting point.

<img src="https://drive.google.com/uc?export=view&id=130x9x3F9KIn9Ki7d4Yc_SJk73vldaIMj" width="300">

## Quickstart

### 1) Create a Telegram Bot

You can follow this guide to build a Python Telegram Bot:

[How to Create a Telegram Bot using Python
](https://www.freecodecamp.org/news/how-to-create-a-telegram-bot-using-python/)

Here I will give you the main steps:

1) Search for **@botfather** in Telegram.
2) Start a conversation with BotFather by clicking on the **Start** button.
3) Type **/newbot**, and follow the prompts to set up a new bot.
4) Type the name you want to give the bot.
5) Type the username you want to give the bot.
6) The BotFather will finally answer with a token that we can use to access the HTTP API. Store the token because we
   will need to use it later.

You can now start a conversation with your bot
by searching for the username on Telegram.

### 2) LLM inference on Beam

As for hosting the llm inference the best option I found for now
is [Beam Cloud](https://www.beam.cloud/). Their compute prices are among the cheapest and
they offer 10 hours of free compute with nice GPUs. The offer free
storage, which is highly appreciated.

The chatbot is built using langchain and huggingface. So if you want
to the [Llama 2](https://huggingface.co/meta-llama/Llama-2-7b-chat) family of models you will need to require access to
the models.
It is very easy to do and they are really quick at approving the request.

TODO I used a couple of sources to put together langchain and HF,
I will add them ASAP.

If you want to use gated models you will need to set an hugging face token.
This is built in the code, I will fix it in the next days.

This is a guide to generate the token:

[HuggingFace User access tokens
](https://huggingface.co/docs/hub/security-tokens)

Once you have created your account, no payment method required,
go to the dashboard and under the Settings tab on the right
menu you can find the Secrets.
If you are using a model like llama 2 that requires an hugging face
token then you need to set the **HF_TOKEN** variable with the hugging face token.

Then you can do everything locally. Move to the
lm subdirectory.

```shell
cd ./src/telegram_llm_bot/shared/llm/beam
```

Follow the Beam installation guide [Beam Installation](https://docs.beam.cloud/getting-started/installation).

Inside the app.py file you can modify the following
variables or leave them as they are. I will soon move them
to a configuration file:

```python
HF_CACHE = "./models"
MODEL_ID = "meta-llama/Llama-2-7b-chat-hf"
APP_NAME = "travel-guru"
GPU = "T4"
MEMORY = "16Gi"
```

You are ready to deploy the app:

```shell
beam deploy app.py
```

The app should be up and running now. Go to the Beam Dashboard
and under the Apps tab you can find your app.

### 3) Host the Telegram bot

You can host your bot for free on a free tier EC2 instance. This is
a guide you can follow:

[Tutorial: Get started with Amazon EC2 Linux instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html)

During the creation of the instance you have to
remember to create a key pair that you will use to connect
via ssh to your instance remotely.

I recommend to set Ubuntu as OS.

Once you set the key pair, the .pem will be automatically downloaded.

Now you can connect to the ec2 instance via command line using ssh:

```shell
ssh -i "{filename}.pem" ubuntu@{address}.{region}.compute.amazonaws.com
```

Clone this repository on the ec2 instance. We will only need the bot folder, we do need the rest,
so I will probably separate it from the rest in the future, for now this is
not a big problem:

```shell
git clone https://github.com/ma2za/telegram-llm-bot.git
```

Move to the bot directory

```shell
cd telegram-llm-bot
```

Create a .env file to set the environment variables common to all your bots

```shell
touch .env
```

Via nano modify the content of the .env with the following content.

```shell
MONGO_HOST=telegram-mongo
MONGO_PORT=27017
```

This is required to set up a MongoDB database to store the conversations.

Create another .env file specific for a bot to set the environment variables

```shell
touch ./src/telegram_llm_bot/bots/base_chatbot/.env
```

Via nano modify the content of the .env with the following content.

```shell
TELEGRAM_BOT_TOKEN =
BEAM_TOKEN =
BEAM_URL = https://apps.beam.cloud/{something}
SETTINGS_FILE=telegram_llm_bot.bots.base_chatbot.settings
BOT_NAME=travel-guru
```

**TELEGRAM_BOT_TOKEN** is the token we received earlier from the BotFather.

**BEAM_TOKEN**: under **API Keys** in the Beam app dashboard
you can generate a Beam token.

**BEAM_URL** is obtained from the overview of the app
where you can click on Call API and there you can easily find out the url

We can finally use docker compose to build images and run the containers.

Install Docker and Docker compose. Here is the official guide:

[Install Docker Engine on Ubuntu
](https://docs.docker.com/engine/install/ubuntu/)

Build, create and start the containers:

```shell
sudo docker compose up -d --build
```

We are done here!

The system prompts are contained in **config.yml**.

You are ready to chat! 🚀🚀🚀🚀🚀

<img src="https://drive.google.com/uc?export=view&id=1EQt9KahzYwWEqOiQMaOrjpRxxZ2IsaoD" width="300">
