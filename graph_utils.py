import networkx as nx
import xml.etree.ElementTree as ET
import html
import os
import urllib.request
import urllib.parse
import ssl
import base64
from typing import Union, Sequence, List, Dict, Any

# --- IMPORTS FOR LIVE FETCHING ---
try:
    import Edging
    from rcon_bridge_1_0_0.rcon_bridge import Rcon_reciever
except ImportError:
    print("Warning: Could not import 'Edging' or 'rcon_bridge'. Ensure they are in the python path.")

# --- CONFIG ---
# Factorio tile = 1 unit. Scale up for graph pixels.
scale_factor = 64

# SSL Context to bypass cert errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Dictionary to store unique resources {machine_name: base64_string}
resources_map = {}


def get_base64_image(machine_name):
    """Downloads image, returns base64 string. Caches results."""
    if machine_name in resources_map:
        return resources_map[machine_name]

    # Name cleaning
    if "turbo" in machine_name:
        fallback_name = machine_name.replace("turbo", "express")
        formatted_name = fallback_name.replace('-', '_').capitalize()
    if "long-handed-inserter" in machine_name:
        formatted_name = "Long-handed_inserter"
    else:
        formatted_name = machine_name.replace('-', '_').capitalize()

    remote_url = f"https://wiki.factorio.com/images/{formatted_name}.png"

    try:
        print(f"Downloading & Embedding: {formatted_name}...")
        req = urllib.request.Request(remote_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response:
            image_data = response.read()
            # Encode to base64
            b64_str = base64.b64encode(image_data).decode('utf-8')
            resources_map[machine_name] = b64_str
            return b64_str
    except Exception as e:
        print(f"Error downloading {formatted_name}: {e}")
        return None


"""Deprecated Function we keep around for Lookup purposes"""


def save_graph_ml(G, labels: Union[Sequence, 'torch.Tensor'], label_name: str, save_path: str):
    """
    Attach node labels (predicted or true) to a copy of G and write as GraphML.
    labels: 1D tensor/list/array aligned with integer node ids.
    """
    try:
        import torch
        if isinstance(labels, torch.Tensor):
            labels_list = labels.view(-1).tolist()
        else:
            labels_list = list(labels)
    except ImportError:
        labels_list = list(labels)

    G_copy = G.copy()
    for i, node in enumerate(G_copy.nodes()):
        if i < len(labels_list):
            G_copy.nodes[node][label_name] = str(int(labels_list[i]))
        else:
            G_copy.nodes[node][label_name] = "0"
    nx.write_graphml(G_copy, save_path)
    print(f"Saved graph to {save_path}")


def create_factorio_graphml(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]],
                            file_name: str = 'yED_Factory.graphml'):
    """
    Generates a GraphML file compatible with yEd, containing embedded images for nodes
    and directed edges based on the logic from Edging.py.
    """

    # --- GRAPHML HEADER ---
    header = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" 
    xmlns:y="http://www.yworks.com/xml/graphml" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd">
  <key for="node" id="d_graphics" yfiles.type="nodegraphics"/>
  <key for="edge" id="d_edge_graphics" yfiles.type="edgegraphics"/>
  <key for="graphml" id="d_resources" yfiles.type="resources"/>
  <graph edgedefault="directed" id="G">
"""

    nodes_xml = ""
    # Coordinate lookup to map (x, y) -> "n0", "n1", etc.
    coord_to_id = {}

    print(f"Generating XML for {len(nodes)} nodes...")
    for i, entity in enumerate(nodes):
        machine_name = entity.get('machine_name', 'unknown')

        # Prefetch image
        get_base64_image(machine_name)

        x = entity.get('x', 0)
        y = entity.get('y', 0)

        # Store mapping for edge generation
        coord_to_id[(x, y)] = f"n{i}"

        x_pos = x * scale_factor
        y_pos = y * scale_factor

        label = machine_name
        if 'recipe_name' in entity and entity['recipe_name'] != 'No Recipe':
            label += f"\n({entity['recipe_name']})"

        nodes_xml += f"""
    <node id="n{i}">
      <data key="d_graphics">
        <y:ImageNode>
          <y:Geometry height="50.0" width="50.0" x="{x_pos}" y="{y_pos}"/>
          <y:Fill color="#FFFFFF" transparent="true"/>
          <y:BorderStyle hasColor="false" type="line" width="1.0"/>
          <y:NodeLabel visible="true" alignment="center" autoSizePolicy="content" fontFamily="Dialog" fontSize="12" fontStyle="plain" modelName="sandwich" modelPosition="s">{html.escape(label)}</y:NodeLabel>
          <y:Image alphaImage="true" refid="{machine_name}"/>
        </y:ImageNode>
      </data>
    </node>"""

    edges_xml = ""
    print(f"Generating XML for {len(edges)} edges...")

    for i, edge in enumerate(edges):
        # Extract coordinates from Edging.py format
        src_coord = (edge['from_x'], edge['from_y'])
        tgt_coord = (edge['to_x'], edge['to_y'])

        # Check if both nodes exist in our node list
        if src_coord in coord_to_id and tgt_coord in coord_to_id:
            src_id = coord_to_id[src_coord]
            tgt_id = coord_to_id[tgt_coord]

            # Create yEd styled edge with standard arrow
            edges_xml += f"""
    <edge id="e{i}" source="{src_id}" target="{tgt_id}">
      <data key="d_edge_graphics">
        <y:PolyLineEdge>
          <y:Path sx="0.0" sy="0.0" tx="0.0" ty="0.0"/>
          <y:LineStyle color="#000000" type="line" width="1.0"/>
          <y:Arrows source="none" target="standard"/>
          <y:BendStyle smoothed="false"/>
        </y:PolyLineEdge>
      </data>
    </edge>"""

    # --- RESOURCES BLOCK ---
    resources_xml = "<data key=\"d_resources\">\n<y:Resources>\n"
    for name, b64_data in resources_map.items():
        if b64_data:
            resources_xml += f"""<y:Resource id="{name}" type="java.awt.image.BufferedImage" xml:space="preserve">{b64_data}</y:Resource>\n"""
    resources_xml += "</y:Resources>\n</data>\n"

    footer = """
  </graph>
  %s
</graphml>
""" % resources_xml

    # --- WRITE FILE ---
    with open(file_name, 'w') as f:
        f.write(header + nodes_xml + edges_xml + footer)

    print("-" * 30)
    print(f"Success! Created '{file_name}' with {len(nodes)} nodes and {len(edges)} edges.")


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # 1. Setup Connection
    # Uses default host="localhost", port=27015, password="eenie7Uphohpaim" from rcon_bridge.py
    receiver = Rcon_reciever()

    try:
        print("Connecting to Factorio RCON...")
        receiver.connect()

        # 2. Fetch Nodes (Entities)
        print("Scanning entities...")
        nodes_data = receiver.scan_entities_boundingboxes()

        if not nodes_data:
            print("No entities found in the scan area.")
        else:
            print(f"Found {len(nodes_data)} entities.")

            # 3. Fetch Edges (Logic from Edging.py)
            # Note: This calls scan_entities_boundingboxes internally again,
            # but ensures we use the exact logic defined in Edging.py
            print("Calculating edges...")
            edges_data = Edging.translateEntitesToEdges(receiver)

            if edges_data is None:
                edges_data = []

            # 4. Generate GraphML
            create_factorio_graphml(nodes_data, edges_data, 'yED_Factory.graphml')

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        receiver.disconnect()
        print("RCON disconnected.")