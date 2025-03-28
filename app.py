import streamlit as st
import json
from utils import generate_graph_data
from llm_utils import call_llm
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(page_title="Knowledge Graph Generator", layout="wide")
# Set page title
st.title("Knowledge Graph Generator")

# Add description
st.write("Please enter the text below for knowledge graph extraction.")

# Add text input area
text_input = st.text_area("Input Text", height=200)

# Initialize session state
if 'graph_data' not in st.session_state:
    st.session_state.graph_data = None
if 'agraph_config' not in st.session_state:
    st.session_state.agraph_config = None
if 'graph_ready' not in st.session_state:
    st.session_state.graph_ready = False

# Initialize session state for API key, supplier and temperature
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'current_supplier' not in st.session_state:
    st.session_state.current_supplier = 'zhipu'  # Default to zhipu
if 'temperature' not in st.session_state:
    st.session_state.temperature = 0.1  # Default temperature

def prepare_graph_visualization(nodes_data, edges_data):
    """Prepare graph visualization data and config"""
    # Convert to agraph format nodes and edges
    nodes = [
        Node(
            id=str(node['id']),  # Ensure id is string
            label=str(node['label']),
            size=25,
            color=f"#{hash(str(node['group'])) % 0xFFFFFF:06x}"
        ) for node in nodes_data
    ]
    
    edges = [
        Edge(
            source=str(edge['from']),  # Ensure source is string
            target=str(edge['to']),    # Ensure target is string
            label=str(edge['label'])
        ) for edge in edges_data
    ]

    # Configure graph display
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

# Add extract button
def extract_knowledge():
    if not text_input:
        st.warning("Please enter text first.")
    else:
        # with st.spinner('Extracting knowledge graph...'):
        try:
            # Call OpenAI API to generate nodes and edges
            nodes_data, edges_data = generate_graph_data(text_input)
            
            if not nodes_data or not edges_data:
                st.warning("Failed to extract valid knowledge graph. Please modify your input text.")
                st.session_state.graph_ready = False
            else:
                # Store graph data in session state
                st.session_state.graph_data = (nodes_data, edges_data)
                # Prepare visualization data
                nodes, edges, config = prepare_graph_visualization(nodes_data, edges_data)
                st.session_state.agraph_config = {
                    'nodes': nodes,
                    'edges': edges,
                    'config': config
                }
                st.session_state.graph_ready = True
                # st.success("Knowledge extraction completed! Click 'Show Graph' to view the result.")
                
        except Exception as e:
            st.error(f"Error during knowledge extraction: {str(e)}")
            st.session_state.graph_ready = False
    return nodes_data, edges_data


if st.button("Extract Knowledge"):
    with st.spinner('Extracting knowledge graph...'):
        nodes_data, edges_data = extract_knowledge()

# if st.button("Show Graph") or st.session_state.graph_ready:
    st.write("Showing graph...")
    with st.expander("Graph", expanded=True):
        st.write("Nodes:")
        st.write(nodes_data)
        st.write("Edges:")
        st.write(edges_data)
        # st.write(st.session_state.agraph_config['nodes'])
        # st.write(st.session_state.agraph_config['edges'])
        # st.write(st.session_state.agraph_config['config'])
    try:
        # Display graph using stored configuration
        return_value = agraph(
            nodes=st.session_state.agraph_config['nodes'],
            edges=st.session_state.agraph_config['edges'],
            config=st.session_state.agraph_config['config']
        )
            
    except Exception as e:
        st.error(f"Error displaying knowledge graph: {str(e)}")

if not st.session_state.graph_ready:
    st.warning("Please extract knowledge first.")

def setup_sidebar():
    """Setup sidebar for API key inputs"""
    with st.sidebar:
        st.header("API Configuration")
        
        # Add supplier selection dropdown
        supplier = st.selectbox(
            "Select LLM Provider",
            options=["zhipu", "openai"],
            index=0,  # Default to zhipu
            key="supplier_select"
        )
        st.session_state.current_supplier = supplier
        
        # Add temperature slider
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.temperature,
            step=0.1,
            help="Higher values make the output more random, lower values make it more focused and deterministic"
        )
        st.session_state.temperature = temperature
        
        st.markdown("---")  # Add a divider
        
        # Single API key input
        api_key = st.text_input(
            f"Enter {supplier.upper()} API Key",
            type="password",
            value=st.session_state.api_key,
            key="api_key_input"
        )
        if api_key:
            st.session_state.api_key = api_key

def main():
    setup_sidebar()
    # Rest of your application code...

if __name__ == "__main__":
    main()


