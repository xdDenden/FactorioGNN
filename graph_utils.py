import networkx as nx
import xml.etree.ElementTree as ET
import html
import os
import urllib.request
import urllib.parse
import ssl
import base64
from typing import Union, Sequence


"""Deprecated Function we keep around for Lookup purposes and was only used as a starting off point"""
def save_graph_ml(G, labels: Union[Sequence, 'torch.Tensor'], label_name: str, save_path: str):
    """
    Attach node labels (predicted or true) to a copy of G and write as GraphML.
    labels: 1D tensor/list/array aligned with integer node ids.
    """
    # Accept torch tensor without importing torch at module top to stay lightweight
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

"""New Function to create GraphML with embedded images from the RCON reciever. This is easier then accessing the world each ai is building in and
allows us to do graph and score analysis without opening the game at larger scales.
Also this allows us to take a more methodical approach to analysing a specific factory. 
This data is from the exampleFactory savefile and can be replace with the file generated from any other rconreciever Output

The Images get embedded into the graph because yEd is weird sometimes. This ensures it working."""
data = [{'machine_name': 'transport-belt', 'x': -28.5, 'y': -26.5, 'rotation': 12},
        {'machine_name': 'express-transport-belt', 'x': -26.5, 'y': -26.5, 'rotation': 12},
        {'machine_name': 'fast-transport-belt', 'x': -27.5, 'y': -26.5, 'rotation': 8},
        {'machine_name': 'turbo-transport-belt', 'x': -25.5, 'y': -26.5, 'rotation': 0},
        {'machine_name': 'inserter', 'x': -20.5, 'y': -26.5, 'status': 54, 'rotation': 0, 'energy': 'False'},
        {'machine_name': 'burner-inserter', 'x': -21.5, 'y': -26.5, 'status': 32, 'rotation': 0, 'energy': 'True'},
        {'machine_name': 'steam-engine', 'x': -16.5, 'y': -26.5, 'status': 5, 'rotation': 0},
        {'machine_name': 'offshore-pump', 'x': -5.5, 'y': -27.5, 'status': 1, 'rotation': 8},
        {'machine_name': 'pipe', 'x': -3.5, 'y': -26.5}, {'machine_name': 'small-electric-pole', 'x': -0.5, 'y': -26.5},
        {'machine_name': 'pipe-to-ground', 'x': -1.5, 'y': -26.5, 'rotation': 8},
        {'machine_name': 'medium-electric-pole', 'x': 0.5, 'y': -26.5},
        {'machine_name': 'assembling-machine-1', 'x': -46.5, 'y': -25.5, 'status': 54, 'energy': 'False',
         'recipe_name': 'advanced-circuit', 'is_crafting': 'False', 'products_finished': 0},
        {'machine_name': 'assembling-machine-2', 'x': -43.5, 'y': -25.5, 'status': 54, 'energy': 'False',
         'recipe_name': 'iron-gear-wheel', 'is_crafting': 'False', 'products_finished': 0},
        {'machine_name': 'assembling-machine-3', 'x': -40.5, 'y': -25.5, 'status': 54, 'energy': 'False',
         'recipe_name': 'electronic-circuit', 'is_crafting': 'False', 'products_finished': 0},
        {'machine_name': 'stone-furnace', 'x': -38, 'y': -26, 'status': 53, 'energy': 'False',
         'recipe_name': 'No Recipe', 'is_crafting': 'False', 'products_finished': 0},
        {'machine_name': 'steel-furnace', 'x': -36, 'y': -26, 'status': 53, 'energy': 'False',
         'recipe_name': 'No Recipe', 'is_crafting': 'False', 'products_finished': 0},
        {'machine_name': 'burner-mining-drill', 'x': -34, 'y': -26, 'status': 53, 'rotation': 8, 'energy': 'False',
         'mining_target': 'iron-ore'},
        {'machine_name': 'electric-mining-drill', 'x': -30.5, 'y': -25.5, 'status': 54, 'rotation': 8,
         'energy': 'False', 'mining_target': 'iron-ore'},
        {'machine_name': 'underground-belt', 'x': -28.5, 'y': -25.5, 'rotation': 8},
        {'machine_name': 'express-underground-belt', 'x': -26.5, 'y': -25.5, 'rotation': 8},
        {'machine_name': 'fast-underground-belt', 'x': -27.5, 'y': -25.5, 'rotation': 8},
        {'machine_name': 'turbo-underground-belt', 'x': -25.5, 'y': -25.5, 'rotation': 0},
        {'machine_name': 'chemical-plant', 'x': -23.5, 'y': -25.5, 'status': 54, 'rotation': 8, 'energy': 'False',
         'recipe_name': 'heavy-oil-cracking', 'is_crafting': 'False', 'products_finished': 0},
        {'machine_name': 'bulk-inserter', 'x': -21.5, 'y': -24.5, 'status': 54, 'rotation': 0, 'energy': 'False'},
        {'machine_name': 'fast-inserter', 'x': -20.5, 'y': -25.5, 'status': 54, 'rotation': 0, 'energy': 'False'},
        {'machine_name': 'long-handed-inserter', 'x': -21.5, 'y': -25.5, 'status': 54, 'rotation': 0,
         'energy': 'False'}, {'machine_name': 'boiler', 'x': -19, 'y': -25.5, 'status': 53, 'rotation': 12},
        {'machine_name': 'oil-refinery', 'x': -12.5, 'y': -25.5, 'status': 54, 'rotation': 8, 'energy': 'False',
         'recipe_name': 'coal-liquefaction'},
        {'machine_name': 'lab', 'x': -8.5, 'y': -25.5, 'status': 20, 'energy': 'True'},
        {'machine_name': 'pipe', 'x': -3.5, 'y': -24.5}, {'machine_name': 'pipe', 'x': -3.5, 'y': -25.5},
        {'machine_name': 'pipe-to-ground', 'x': -1.5, 'y': -25.5, 'rotation': 0},
        {'machine_name': 'big-electric-pole', 'x': 2, 'y': -26}, {'machine_name': 'substation', 'x': 4, 'y': -26},
        {'machine_name': 'splitter', 'x': -28.5, 'y': -24, 'rotation': 12},
        {'machine_name': 'express-splitter', 'x': -26.5, 'y': -24, 'rotation': 12},
        {'machine_name': 'fast-splitter', 'x': -27.5, 'y': -24, 'rotation': 12},
        {'machine_name': 'turbo-splitter', 'x': -25.5, 'y': -24, 'rotation': 12}]

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


# --- GRAPHML PARTS ---

header = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" 
    xmlns:y="http://www.yworks.com/xml/graphml" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd">
  <key for="node" id="d_graphics" yfiles.type="nodegraphics"/>
  <key for="graphml" id="d_resources" yfiles.type="resources"/>
  <graph edgedefault="directed" id="G">
"""

nodes_xml = ""

for i, entity in enumerate(data):
    machine_name = entity.get('machine_name', 'unknown')

    # Prefetch the image data to populate resources_map
    get_base64_image(machine_name)

    x_pos = entity.get('x', 0) * scale_factor
    y_pos = entity.get('y', 0) * scale_factor

    label = machine_name
    if 'recipe_name' in entity and entity['recipe_name'] != 'No Recipe':
        label += f"\n({entity['recipe_name']})"

    # In yEd, we reference the resource by ID (we will use machine_name as ID)
    nodes_xml += f"""
    <node id="n{i}">
      <data key="d_graphics">
        <y:ImageNode>
          <y:Geometry height="50.0" width="50.0" x="{x_pos}" y="{y_pos}"/>
          <y:Fill color="#FFFFFF" transparent="true"/>
          <y:BorderStyle hasColor="false" type="line" width="1.0"/>
          <y:NodeLabel visible="true" alignment="center" autoSizePolicy="content" fontFamily="Dialog" fontSize="12" fontStyle="plain" modelName="sandwich" modelPosition="s">{label}</y:NodeLabel>
          <y:Image alphaImage="true" refid="{machine_name}"/>
        </y:ImageNode>
      </data>
    </node>"""

# --- CONSTRUCT RESOURCE BLOCK ---
# This block holds the actual image data encoded in base64
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
file_name = 'yED_Factory.graphml'
with open(file_name, 'w') as f:
    f.write(header + nodes_xml + footer)

print("-" * 30)
print(f"Success! Created '{file_name}'")