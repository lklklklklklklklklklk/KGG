import json
from llm_utils import call_llm
import streamlit as st

def detect_language(text):
    """Detect the primary language of the input text"""
    # Simple language detection based on character sets
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    english_chars = len([c for c in text if c.isascii() and c.isalpha()])

    return 'chinese' if chinese_chars > english_chars else 'english'


def get_system_prompt(language, is_extension=False):
    """Get system prompt based on language and whether it's an extension"""
    if language == 'chinese':
        if is_extension:
            return  """You are a professional text analysis assistant. Please analyze the input textbook table of contents, extract the subsections, key concepts, and knowledge points, and identify their relationships. Then generate a knowledge graph where the central node is the chapter title, the first-level nodes are subsection titles, and the second-level nodes include knowledge points, concepts, and so on. After the subgraph is generated, treat it as an extension of the knowledge graph, and connect its central chapter node to the corresponding chapter node in the input knowledge graph as the same node.


You must output ONLY a JSON object in the following format, with NO additional text or explanation:

{
    "nodes": [
        {
            "id": "1",           // Must be a unique string
            "label": "概念1",     // 概念的中文名称
            "group": "类别1"      // Category in Chinese
        }
    ],
    "edges": [
        {
            "from": "1",         // Must match an existing node id
            "to": "2",           // Must match an existing node id
            "label": "包含"       // Relationship description in Chinese
        }
    ]
}

Requirements:
1.Only output the JSON object. Do NOT include any other text or explanation.
2.  Only use the following entity types for nodes:
   - 教材
   - 章节
   - 小节
   - 知识点
   - 概念
   - 公式/定理/算法
3. Only use the following relationship types for edges:
   - `包含` (用于 教材 → 章节，章节 → 小节)
   - `组成` (用于 小节 → 知识点/概念/公式)
   - `先后` (用于 有时间或步骤顺序的知识点)
   - `因果` (用于 逻辑推导关系)
4.  All node labels and edge descriptions must be written in Chinese using natural, idiomatic, and accurate expressions.
5.  The output must be a valid and complete JSON structure. Ensure all {} and [] brackets are properly closed.
6.  Similar concepts should be grouped under the same category, avoiding duplication or inconsistent naming.
7. Edge descriptions must be clear, meaningful, and logically accurate.
8.  The generated subgraph must have its own central node, typically a "章节" (chapter) node, and it must connect to related concepts such as subsections and knowledge points.
10. Each subgraph must follow a clear hierarchical structure:
Chapter → Subsections → Concepts / Knowledge Points / Formulas.
11. All node IDs must be unique strings.
12. If merging the generated subgraph with the input graph causes conflicts, you must reassign IDs to ensure uniqueness.
13.All from and to fields in the edges must reference existing node IDs in the graph.
14. You MUST NOT create a new node for the chapter if it already exists in the input JSON graph. Instead, you MUST use the same node ID and label as the existing chapter node in the input graph.
15. The generated subgraph must use that existing chapter node as the center and connect all its new subsections, concepts, and knowledge points under it.
16. For example, if the input graph contains a chapter node with ID "3" and label "数据链路层", and the text is about that chapter, then your generated subgraph must use the existing ID "3" as the central node and attach all new content to it. Do NOT create a new node with a different ID or duplicate label.The chapter node already exists in the input graph, so you MUST NOT recreate it.

Before finalizing your output, review all nodes to ensure there are no duplicate IDs. If multiple nodes share the same ID, you must keep only one and discard the others.
"""

        else:
            return  """You are a professional text analysis assistant. Please analyze the input textbook table of contents, extract the chapters and their relationships, and generate a preliminary knowledge graph with the textbook name as the central node and each chapter name as a chapter node.
You must output ONLY a JSON object in the following format, with NO additional text or explanation:

{
    "nodes": [
        {
            "id": "1",           // Must be a unique string
            "label": "章节名",     // Chapter  name in Chinese
            "group": "类别1"      // Category in Chinese
        }
    ],
    "edges": [
        {
            "from": "1",         // Must match an existing node id
            "to": "2",           // Must match an existing node id
            "label": "包含"       // Relationship description in Chinese
        }
    ]
}

Requirements:
1. Output ONLY the JSON object, no other text
2. All node IDs must be unique strings
3. All 'from' and 'to' in edges must reference existing node IDs
4. All labels and descriptions MUST be in Chinese
5. The output must be valid JSON format
6. Extract ALL chapters every chapter MUST appear as a node.
8. Use natural and idiomatic Chinese expressions
9. Ensure relationship descriptions are clear and meaningful
10. The textbook name must be the central node and connect only to chapter nodes.
11. Only use the following entity types for nodes:
   - 教材
   - 章节
12. Only use the following relationship types for edges:
   - `包含` (用于 教材 → 章节)
13.The output must be in a valid JSON format with complete and properly closed `{}` and `[]` brackets.

DO NOT include any explanations or markdown formatting in the output."""


def generate_graph_data(text, json_input=None):
    """Call OpenAI API to generate graph nodes and edges data"""

    # Detect the language of input text
    language = detect_language(text)

    # Determine if we need to extend an existing graph
    is_extension = False
    if json_input:
        is_extension = True

    # Get appropriate system prompt based on language and extension flag
    system_msg = get_system_prompt(language, is_extension)

    user_msg = "Please analyze the following text and generate relationship graph data:\n" + text

    try:
        # Call OpenAI API
        output = call_llm(system_msg, user_msg, st.session_state.current_model)
        if not output:
            raise ValueError("API returned empty response")

        # Clean potential extra content from output
        output = output.strip()
        if output.startswith("```json"):
            output = output[7:]
        if output.endswith("```"):
            output = output[:-3]
        output = output.strip()

        # Parse JSON data
        result = json.loads(output)

        # Validate data format
        if not isinstance(result, dict):
            raise ValueError("Response is not a JSON object")
        if 'nodes' not in result or 'edges' not in result:
            raise ValueError("Missing required 'nodes' or 'edges' fields")
        if not isinstance(result['nodes'], list) or not isinstance(result['edges'], list):
            raise ValueError("'nodes' or 'edges' is not an array")
        if len(result['nodes']) < 3:
            raise ValueError("At least 3 nodes are required")

        # Validate nodes and edges data
        node_ids = set()
        groups = set()
        for node in result['nodes']:
            if not all(k in node for k in ('id', 'label', 'group')):
                raise ValueError("Invalid node format - missing required fields")
            if not all(isinstance(node[k], str) for k in ('id', 'label', 'group')):
                raise ValueError("Node fields must be strings")
            if str(node['id']) in node_ids:
                raise ValueError(f"Duplicate node ID found: {node['id']}")
            node_ids.add(str(node['id']))
            groups.add(node['group'])

        for edge in result['edges']:
            if not all(k in edge for k in ('from', 'to', 'label')):
                raise ValueError("Invalid edge format - missing required fields")
            if not all(isinstance(edge[k], str) for k in ('from', 'to', 'label')):
                raise ValueError("Edge fields must be strings")
            if str(edge['from']) not in node_ids:
                raise ValueError(f"Edge references non-existent source node: {edge['from']}")
            if str(edge['to']) not in node_ids:
                raise ValueError(f"Edge references non-existent target node: {edge['to']}")

        # return result['nodes'], result['edges']
        return result['nodes'], result['edges'], system_msg, st.session_state.current_model


    except json.JSONDecodeError as je:
        st.error(f"JSON parsing error: {str(je)}\nActual output: {output}")
        return [], []
    except Exception as e:
        st.error(f"Error generating graph data: {str(e)}")
        return [], []
