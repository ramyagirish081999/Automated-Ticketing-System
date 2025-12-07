import streamlit as st
import asyncio
from agent import *
import time
from backend import *

st.title("Ticketing Chat Assistant")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Type in your query")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Processing your query"):
            result = asyncio.run(call_agent(user_input))

        agent_reponse = str(result.response) if hasattr(result, "response") else str(result)

        st.write(agent_reponse)

    st.session_state["messages"].append({"role": "assistant", "content": agent_reponse})

if "last_main_run" not in st.session_state:
    st.session_state["last_main_run"] = 0

current_time = time.time()
two_minutes = 120

if current_time - st.session_state["last_main_run"] >= two_minutes:
    with st.spinner("Updating ticket status"):
        json_updater()
    st.session_state["last_main_run"] = current_time
