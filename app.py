import streamlit as st
import json
import os
from datetime import datetime
from utils import generate_graph_data  # Updated to return (nodes, edges, system_msg, model_name)
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(page_title="Knowledge Graph Generator", layout="wide")
st.title("Knowledge Graph Generator")
st.write("Please enter the text below for knowledge graph extraction.")

text_input = st.text_area("Input Text", height=200)
json_input = st.text_area("Input Previous Knowledge Graph (JSON)", height=200, help="Paste the previous knowledge graph JSON here.")

if 'graph_data' not in st.session_state:
    st.session_state.graph_data = None
if 'agraph_config' not in st.session_state:
    st.session_state.agraph_config = None
if 'graph_ready' not in st.session_state:
    st.session_state.graph_ready = False

nodes_data = []
edges_data = []

model_options = [
    "deepseek-r1-250120",
    "gpt-4o-2024-08-06"
]

st.sidebar.header("Model Selection")
selected_model = st.sidebar.selectbox("Choose your model:", model_options, index=model_options.index(
    st.session_state.current_model) if 'current_model' in st.session_state else 0)
st.session_state.current_model = selected_model


def prepare_graph_visualization(nodes_data, edges_data):
    nodes = [
        Node(
            id=str(node['id']),
            label=str(node['label']),
            size=25,
            color=f"#{hash(str(node['group'])) % 0xFFFFFF:06x}"
        ) for node in nodes_data
    ]

    edges = [
        Edge(
            source=str(edge['from']),
            target=str(edge['to']),
            label=str(edge['label'])
        ) for edge in edges_data
    ]

    config = Config(
        width=1000,
        height=500,
        directed=True,
        physics=True,
        hierarchical=True,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=True,
        node={'labelProperty': 'label'},
        link={'labelProperty': 'label', 'renderLabel': True}
    )

    return nodes, edges, config


def extract_knowledge():
    if not text_input:
        st.warning("Please enter text first.")
        return [], [], '', ''

    try:
        nodes_data, edges_data, system_msg, model_name = generate_graph_data(text_input)
        if not nodes_data or not edges_data:
            st.warning("Failed to extract valid knowledge graph. Please modify your input text.")
            st.session_state.graph_ready = False
            return [], [], '', ''

        st.session_state.graph_data = (nodes_data, edges_data)
        nodes, edges, config = prepare_graph_visualization(nodes_data, edges_data)
        st.session_state.agraph_config = {
            'nodes': nodes,
            'edges': edges,
            'config': config
        }
        st.session_state.graph_ready = True
        return nodes_data, edges_data, system_msg, model_name
    except Exception as e:
        st.error(f"Error during knowledge extraction: {str(e)}")
        return [], [], '', ''


def parse_and_merge_json_input():
    try:
        if json_input:
            graph_data = json.loads(json_input)
            nodes_data = graph_data.get("nodes", [])
            edges_data = graph_data.get("edges", [])

            new_nodes_data, new_edges_data, system_msg, model_name = generate_graph_data(text_input, json_input)

            nodes_data.extend(new_nodes_data)
            edges_data.extend(new_edges_data)

            return nodes_data, edges_data, system_msg, model_name
    except json.JSONDecodeError:
        st.error("Invalid JSON format. Please check your input.")
        return [], [], '', ''


def save_graph_to_file(nodes_data, edges_data):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"knowledge_graph_{timestamp}.json"

    graph_data = {
        "nodes": nodes_data,
        "edges": edges_data
    }

    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=4)

    st.success(f"Graph saved as {file_name}")
    return file_name


if st.button("Generate and Save Graph"):
    with st.spinner('Generating graph...'):
        if json_input:
            nodes_data, edges_data, system_msg, model_name = parse_and_merge_json_input()
        else:
            nodes_data, edges_data, system_msg, model_name = extract_knowledge()

        if nodes_data and edges_data:
            file_name = save_graph_to_file(nodes_data, edges_data)
            st.write(f"Download the graph file: {file_name}")
            st.download_button("Download JSON File", data=open(file_name, 'rb'), file_name=file_name)

            # ✅ 显示使用的模型和提示词
            with st.expander("🔧 使用配置（提示词 & 模型）", expanded=False):
                st.markdown(f"**使用模型**: `{model_name}`")
                st.markdown("**系统提示词**:")
                st.code(system_msg, language='markdown')


# 渲染 JSON 图谱功能（独立）
st.subheader("Render Graph from JSON Text")
json_input_for_rendering = st.text_area("Enter Graph JSON to Render", height=200, help="Paste the entire graph JSON here.")

if st.button("Render Graph from JSON"):
    if json_input_for_rendering:
        try:
            graph_data = json.loads(json_input_for_rendering)
            nodes_data = graph_data.get("nodes", [])
            edges_data = graph_data.get("edges", [])

            if nodes_data and edges_data:
                st.write("Rendering graph...")
                nodes, edges, config = prepare_graph_visualization(nodes_data, edges_data)
                return_value = agraph(
                    nodes=nodes,
                    edges=edges,
                    config=config
                )
            else:
                st.error("Invalid graph data.")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format: {e}")
    else:
        st.error("Please input a valid JSON graph.")
