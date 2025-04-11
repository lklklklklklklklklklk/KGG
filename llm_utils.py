import openai
import os
import json
import streamlit as st
# API Keys (place your keys here)
API_KEYS = {
    "openai": "sk-Q5JgeDCDMMn2JaRINmHcxRyVK8WNjE6KPGBXdjFc55D521A501Ab4b2393Db78C71d395308"
}

# Initialize client
client = openai.Client(api_key=API_KEYS["openai"], base_url="http://14.103.16.83:35434/v1")

def call_llm(system_msg, user_msg, model_name="deepseek-r1-250120"):
    """Call the LLM API and get the response."""
    st.info(system_msg, icon="🔥")
    # st.info(user_msg, icon="🔥")
    st.info(f"当前模型: {model_name}", icon="ℹ️")
    try:
        # Call the appropriate model based on the model_name
        if model_name == "gpt-4o-2024-08-06":
            response = client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ]
            )
        else:  # Default to DeepSeek model
            response = client.chat.completions.create(
                model="deepseek-r1-250120",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ]
            )

        return response.choices[0].message.content

    except Exception as e:
        return f"API call error: {str(e)}"
