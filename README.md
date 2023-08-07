# Free (for the first 10 hours of compute) Telegram Llm Bot 

## Quickstart

This is a guide on how to build a Telegram Bot backed by
an LLM (i.e. llama2-chat, llama2-32k, vicuna). The bot is
hosted on a free tier EC2 instance, the llm inference is hosted on
Beam Cloud as a serverless REST API, which is free for the first 
10 hours of compute.

### 1) Create a Telegram Bot

I tried with PythonAnywhere, but you need to ask them to 
whitelist the Beam endpoints, which they will probably not 
allow.

You can follow this guide to build a Python Telegram Bot:

[How to Create a Telegram Bot using Python
](https://www.freecodecamp.org/news/how-to-create-a-telegram-bot-using-python/)

Here I will give you the main steps:

1) Search for **@botfather** in Telegram.
2) Start a conversation with BotFather by clicking on the **Start** button.
3) Type **/newbot**, and follow the prompts to set up a new bot.
4) Type the name you want to give the bot.
5) Type the username you want to give the bot.
6) The BotFather will finally answer with a token that we can use to access the HTTP API. Store the token because we will need to use it later.

You can now start a conversation with your bot
by searching for the username on Telegram.

### 2) Host the Telegram bot

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
git clone https://github.com/ma2za/telegram-llm-guru.git
```

Move to the bot directory

```shell
cd telegram-llm-guru/src/bot
```

Create a virtual environment

```shell
python3 -m venv venv
```

Activate environment

```shell
source venv/bin/activate
```
Install bot requirements

```shell
pip install -r requirements.txt
```

Create a .env file to set the environment variables

```shell
touch .env
```

Via nano modify the content of the .env with the following content.
**TELEGRAM_BOT_TOKEN** is the token we received earlier from the BotFather.
Later we will also receive a Beam Token, which we will assign to **BEAM_TOKEN** and URL (**BEAM_URL**), 
so for now we only set the telegram token:

```shell
TELEGRAM_BOT_TOKEN=
```

We can finally launch our bot:

```shell
python3 bot.py &
```

We are done here, we can finally close the shell.

### 3) LLM inference on Beam