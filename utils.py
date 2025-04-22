import json
from llm_utils import call_llm
import streamlit as st

def detect_language(text):
    """Detect the primary language of the input text"""
    # Simple language detection based on character sets
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    english_chars = len([c for c in text if c.isascii() and c.isalpha()])

    return 'chinese' if chinese_chars > english_chars else 'english'


def get_system_prompt(language, is_extension=False, type="subgraph"):
    """Get system prompt based on language and whether it's an extension"""
      # 生成子图
    if type == "subgraph":
        return  """You are a professional text analysis assistant tasked with analyzing a specific chapter from the textbook to extract Chapter, subsections, key concepts, knowledge points, and their relationships. Generate a knowledge graph structured as follows:
Node Types:
章节
小节
知识点
概念
公式/定理/算法

Relationship Types:
包含 (章节 → 小节)
组成 (小节 → 知识点/概念/公式)
先后 (时间或步骤顺序的知识点之间)
因果 (逻辑推导关系)

Output Format (JSON Only, Chinese labels and descriptions):
{
  "nodes": [
    {
      "id": "1",
      "label": "概念1",
      "group": "类别1"
    }
  ],
  "edges": [
    {
      "from": "1",
      "to": "2",
      "label": "包含"
    }
  ]
}

ID Assignment Rules:
Existing chapter nodes use integer IDs ("1", "2", "3", etc.). Do not duplicate.
New subsections under existing chapters:
Chapter "1" subsections: "1.1", "1.2", "1.3", etc.
Chapter "2" subsections: "2.1", "2.2", "2.3", etc.
Continue similarly for other chapters.
Knowledge points, concepts, or formulas under subsections:
Under subsection "1.1": "1.1.1", "1.1.2", etc.
Under subsection "1.1.1": "1.1.1.1", "1.1.1.2", etc.
Continue similarly, maintaining a clear hierarchical structure.

Constraints:
Knowledge points extracted from the current chapter must not be isolated nodes. Each knowledge point must have at least one edge ("包含" or "组成") connecting it directly to a subsection or chapter node.

Final Checks:
1、Ensure all node IDs are unique.
2、"from" and "to" fields must reference existing node IDs.
3、Verify JSON structure correctness and completeness.
"""
    else:
        return  """
Please create a node with ID 0 as the **课程** node. Then, for each **章节** (chapter) node with IDs 1, 2, 3, and 4, generate a **"包含"** edge connecting them to the **课程** (textbook) node with ID 0.
Do NOT regenerate any nodes or edges that already exist in the provided input JSON graph. Specifically, the nodes and edges in the input JSON should remain unchanged. Only generate new nodes and edges to extend the graph based on the provided content.
Example:
Existing node:
Subsection: "id": "1", "label": "第1章", "group": "章节"
Subsection: "id": "2", "label": "第2章", "group": "章节"
Subsection: "id": "3", "label": "第3章", "group": "章节"
Subsection: "id": "4", "label": "第4章", "group": "章节"
From Chapter 1 to Chapter N And so on.

New nodes:
"id": "0", "label": "课程", "group": "教材"

New Edges:
{
  "from": "0",
  "to": "1",
  "label": "包含"
}
{
  "from": "0",
  "to": "2",
  "label": "包含"
}
{
  "from": "0",
  "to": "3",
  "label": "包含"
}
{
  "from": "0",
  "to": "4",
  "label": "包含"
}

Output Format (JSON Only, Chinese labels and descriptions):
{
  "nodes": [
    {
      "id": "1",
      "label": "概念1",
      "group": "类别1"
    }
  ],
  "edges": [
    {
      "from": "1",
      "to": "2",
      "label": "包含"
    }
  ]
}

Final Checks:

1、Ensure all node IDs are unique.
2、"from" and "to" fields must reference existing node IDs.
3、Verify JSON structure correctness and completeness.
4、Do NOT recreate existing nodes or edges in the input JSON.
"""


def generate_graph_data(text, json_input=None, type="subgraph"):
    """Call OpenAI API to generate graph nodes and edges data"""

    # Detect the language of input text
    language = detect_language(text)

    # Determine if we need to extend an existing graph
    is_extension = False
    if json_input:
        is_extension = True
        user_msg = "### 以下是已有知识图谱（JSON 格式），请在此基础上扩展 ###\n"
        user_msg += json_input
        user_msg = "\n\n### Please analyze the following text and generate relationship graph data: ###\n"
        user_msg += text
    else:
        user_msg = "### Please analyze the following text and generate relationship graph data: ###\n"
        user_msg += text
        
    # Get appropriate system prompt based on language and extension flag
    system_msg = get_system_prompt(language, is_extension, type)




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
        # if len(result['nodes']) < 3:
        #     raise ValueError("At least 3 nodes are required")

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
            # if str(edge['from']) not in node_ids:
            #     raise ValueError(f"Edge references non-existent source node: {edge['from']}")
            # if str(edge['to']) not in node_ids:
            #     raise ValueError(f"Edge references non-existent target node: {edge['to']}")

        # return result['nodes'], result['edges']
        return result['nodes'], result['edges'], system_msg, st.session_state.current_model


    except json.JSONDecodeError as je:
        st.error(f"JSON parsing error: {str(je)}\nActual output: {output}")
        return [], []
    except Exception as e:
        st.error(f"Error generating graph data: {str(e)}")
        return [], []
