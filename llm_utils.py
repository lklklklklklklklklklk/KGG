import os
import json
import streamlit as st
from langchain_community.chat_models import AzureChatOpenAI
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.chat_models import ChatOpenAI
import openai
from langchain_core.messages import SystemMessage, HumanMessage
API_KEYS = {
    "zhipu": "0905a059f8b34cdf8ea0ec4476d95309.ThwNU4fpyeNzFNFI",
    "openai": "sk-Q5JgeDCDMMn2JaRINmHcxRyVK8WNjE6KPGBXdjFc55D521A501Ab4b2393Db78C71d395308"
}
# Initialize session state for API key, supplier and temperature
# if 'api_key' not in st.session_state:
#     st.session_state.api_key = ''
if 'current_supplier' not in st.session_state:
    st.session_state.current_supplier = 'openai'  # Default to zhipu
if 'temperature' not in st.session_state:
    st.session_state.temperature = 0.1  # Default temperature

# Azure OpenAI Configuration
AZURE_CONFIGS = {
    "xxx"
}
client = openai.Client(api_key=API_KEYS["openai"], base_url="http://14.103.16.83:35434/v1")
def call_llm(system_msg, user_msg, supplier=st.session_state.current_supplier):
    st.info(system_msg, icon="🔥")
    st.info(user_msg, icon="🔥")
    st.info(f"当前供应商: {supplier}", icon="ℹ️")
    # if not st.session_state.api_key:
    #     raise ValueError(f"{supplier.upper()} API Key not set. Please enter it in the sidebar.")
    if supplier not in API_KEYS:
        raise ValueError(f"API key for {supplier.upper()} is not configured.")

    try:
        if supplier == "openai":
            # model_name = "o1"  # 或者 "o1-mini"
            # api_base = "http://14.103.16.83:35434/v1"
            # st.info(f"使用模型: {model_name}", icon="🤖")
            # st.info(f"连接 API 地址: {api_base}", icon="🌐")
            #
            # llm = ChatOpenAI(
            #     model_name="o1-mini",
            #     openai_api_key=API_KEYS["openai"],
            #     openai_api_base="http://14.103.16.83:35434/v1",
            #     # temperature=st.session_state.temperature,
            #     # max_tokens=None,
            #     # timeout=None,
            #     # max_retries=2
            # )
            #
            # messages = [
            #     SystemMessage(system_msg),
            #     HumanMessage(user_msg)
            # ]
            response = client.chat.completions.create(
                model="deepseek-r1-250120",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ]
            )

            st.success("API 调用成功！")
            return response.choices[0].message.content
        # if supplier == "azure":
        #     os.environ["AZURE_OPENAI_API_KEY"] = API_KEYS["azure"]
        #     os.environ["AZURE_OPENAI_ENDPOINT"] = AZURE_CONFIGS["base_url"]
        #
        #     llm = AzureChatOpenAI(
        #         openai_api_version=AZURE_CONFIGS['api_version'],
        #         azure_endpoint=AZURE_CONFIGS["base_url"],
        #         azure_deployment=AZURE_CONFIGS["model_deployment"],
        #         model=AZURE_CONFIGS["model_name"],
        #         validate_base_url=False,
        #         temperature=st.session_state.temperature,  # Use temperature from session state
        #         max_tokens=None,
        #         timeout=None,
        #         max_retries=2
        #     )
        #
        #     messages = [
        #         ('system', system_msg),
        #         ('human', user_msg)
        #     ]
        elif supplier == "zhipu":
            llm = ChatZhipuAI(
                model='glm-4-flash',
                temperature=st.session_state.temperature,  # Use temperature from session state
                api_key=API_KEYS["zhipu"]
            )
            
            messages = [
                SystemMessage(system_msg),
                HumanMessage(user_msg)
            ]
        else:
            raise ValueError(f'Invalid LLM supplier: {supplier}')

        # Call LLM

        # 测试 API 连接
        st.info("正在调用 LLM...", icon="🚀")
        res = llm.invoke(messages)
        if not res or not res.content:
            raise ValueError("API returned empty response")
            
        output = res.content
        st.success("成功获取 API 响应 ✅")

        # Validate JSON format and structure
        data = json.loads(output)
        if not isinstance(data, dict):
            raise ValueError("API response is not a valid JSON object")
        
        if 'nodes' not in data or 'edges' not in data:
            raise ValueError("API response missing required 'nodes' or 'edges' fields")
            
        if not isinstance(data['nodes'], list) or not isinstance(data['edges'], list):
            raise ValueError("'nodes' and 'edges' must be arrays")
            
        if len(data['nodes']) < 3:
            raise ValueError("At least 3 nodes are required")
            
        # Print output for debugging
        st.write("Extraction result:")
        st.info(output, icon="🎯")
        return output
            
    except json.JSONDecodeError as je:
        st.error(f"Invalid JSON format in API response: {str(je)}")
        return '{"nodes": [], "edges": []}'
    except ValueError as ve:
        st.error(str(ve))
        return '{"nodes": [], "edges": []}'
    except Exception as e:
        st.error(f"API call error: {str(e)}")
        return '{"nodes": [], "edges": []}' 