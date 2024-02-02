import functools
import logging
import threading
import streamsync as ss
import base64

import sys
OPENAI_API_KEY="sk-z5oO REDACTED"

import copy
from openai import OpenAI
import asyncio

client = OpenAI(api_key=OPENAI_API_KEY)

def update_messages(state, user_message: str) -> None:
    """Make OpenAI call and update state in response to streamed reply"""
    logging.info(f"started openai thread with message {user_message} and {len(state['all_messages'])} prior messages")
    # messages = copy.deepcopy(messages)
    state["all_messages"].append(
        {"role": "user",
         "content": user_message,
         "image":b64_image(human=True)})
    state["all_messages"].append({"role": "assistant", "content": "", "image":b64_image(human=False)})

    stream = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=remove_image(state["all_messages"]),
        temperature=0.9,
        stream=True  # again, we set stream=True
       )
    # create variables to collect the stream of chunks
    collected_chunks = []
    collected_messages = []
    # iterate through the stream of events
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            collected_chunks.append(chunk)  # save the event stream
            chunk_message = chunk.choices[0].delta.content  # extract the message
            print(chunk_message, end="")
            sys.stdout.flush()
            collected_messages.append(chunk_message)  # save the message
            state["all_messages"][-1]["content"] = ''.join(collected_messages)
    logging.info(f"reply: {''.join(collected_messages)}")


@functools.lru_cache()
def b64_image(human: bool) -> str:
    path = "static/human_smaller.png" if human else "static/robot_smaller.png"
    with open(path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:image/png;base64,{encoded_string}"

def remove_image(msgs: list) -> list[dict]:
    return [
        {"role": x["role"],
         "content": x["content"],
         }
         for x in msgs
    ]


PROMPT = "You are a tech enthusiast that lives, breathes and dreams about cutting-edge advancements in AI, blockchain and quantum computing. You manage do derail every conversation to be about large language models, blockchains, quantum computers or all three. E.g. when somebody remarks about the weather, you start talking about how smart contracts in Ethereum make requests to weather oracles. You answer in Markdown and like boldface, caps and emojis. This is a coffee machine conversation between distant acquaintances"

MESSAGES = [{"role": "user", "content": PROMPT}]

def on_send_message(state):
    state["visible"] = True
    logging.info("on_send_message")
    if (user_message := state["user_message"]) != "":
        logging.info(f"Got user message: {user_message}")
        state["user_message"] = ""
        thread = threading.Thread(target=update_messages, args=(state, user_message))
        thread.start()


def update_timer(state):
    state["repeater_messages"] = state["all_messages"][1:]

initial_state = ss.init_state({
    "all_messages": MESSAGES,
    "repeater_messages": [],
    "user_message": "",
    "visible": False
})


