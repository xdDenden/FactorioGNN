import rcon_bridge_1_0_0.rcon_bridge

def translateEntitesToEdges(reciever) -> None:
    #raw_entities_BB = reciever.scan_entities_boundingboxes()
    #raw_entities_BB = [{'machine_name': 'electric-mining-drill', 'x': -67.5, 'y': -78.5, 'selection_box': {'left_top': {'y': -80, 'x': -69}, 'right_bottom': {'y': -77, 'x': -66}}}, {'machine_name': 'electric-mining-drill', 'x': -64.5, 'y': -78.5, 'selection_box': {'left_top': {'y': -80, 'x': -66}, 'right_bottom': {'y': -77, 'x': -63}}}, {'machine_name': 'medium-electric-pole', 'x': -69.5, 'y': -77.5, 'selection_box': {'left_top': {'y': -78, 'x': -70}, 'right_bottom': {'y': -77, 'x': -69}}}, {'machine_name': 'transport-belt', 'x': -66.5, 'y': -76.5, 'selection_box': {'left_top': {'y': -77, 'x': -67}, 'right_bottom': {'y': -76, 'x': -66}}}, {'machine_name': 'transport-belt', 'x': -67.5, 'y': -76.5, 'selection_box': {'left_top': {'y': -77, 'x': -68}, 'right_bottom': {'y': -76, 'x': -67}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -76.5, 'selection_box': {'left_top': {'y': -77, 'x': -66}, 'right_bottom': {'y': -76, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -64.5, 'y': -76.5, 'selection_box': {'left_top': {'y': -77, 'x': -65}, 'right_bottom': {'y': -76, 'x': -64}}}, {'machine_name': 'medium-electric-pole', 'x': -62.5, 'y': -76.5, 'selection_box': {'left_top': {'y': -77, 'x': -63}, 'right_bottom': {'y': -76, 'x': -62}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -74.5, 'selection_box': {'left_top': {'y': -75, 'x': -66}, 'right_bottom': {'y': -74, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -75.5, 'selection_box': {'left_top': {'y': -76, 'x': -66}, 'right_bottom': {'y': -75, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -72.5, 'selection_box': {'left_top': {'y': -73, 'x': -66}, 'right_bottom': {'y': -72, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -73.5, 'selection_box': {'left_top': {'y': -74, 'x': -66}, 'right_bottom': {'y': -73, 'x': -65}}}, {'machine_name': 'medium-electric-pole', 'x': -57.5, 'y': -72.5, 'selection_box': {'left_top': {'y': -73, 'x': -58}, 'right_bottom': {'y': -72, 'x': -57}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -70.5, 'selection_box': {'left_top': {'y': -71, 'x': -66}, 'right_bottom': {'y': -70, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -71.5, 'selection_box': {'left_top': {'y': -72, 'x': -66}, 'right_bottom': {'y': -71, 'x': -65}}}, {'machine_name': 'medium-electric-pole', 'x': -69.5, 'y': -69.5, 'selection_box': {'left_top': {'y': -70, 'x': -70}, 'right_bottom': {'y': -69, 'x': -69}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -68.5, 'selection_box': {'left_top': {'y': -69, 'x': -66}, 'right_bottom': {'y': -68, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -69.5, 'selection_box': {'left_top': {'y': -70, 'x': -66}, 'right_bottom': {'y': -69, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -66.5, 'selection_box': {'left_top': {'y': -67, 'x': -66}, 'right_bottom': {'y': -66, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -67.5, 'selection_box': {'left_top': {'y': -68, 'x': -66}, 'right_bottom': {'y': -67, 'x': -65}}}, {'machine_name': 'medium-electric-pole', 'x': -51.5, 'y': -66.5, 'selection_box': {'left_top': {'y': -67, 'x': -52}, 'right_bottom': {'y': -66, 'x': -51}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -64.5, 'selection_box': {'left_top': {'y': -65, 'x': -66}, 'right_bottom': {'y': -64, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -65.5, 'selection_box': {'left_top': {'y': -66, 'x': -66}, 'right_bottom': {'y': -65, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -62.5, 'selection_box': {'left_top': {'y': -63, 'x': -66}, 'right_bottom': {'y': -62, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -63.5, 'selection_box': {'left_top': {'y': -64, 'x': -66}, 'right_bottom': {'y': -63, 'x': -65}}}, {'machine_name': 'medium-electric-pole', 'x': -72.5, 'y': -61.5, 'selection_box': {'left_top': {'y': -62, 'x': -73}, 'right_bottom': {'y': -61, 'x': -72}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -60.5, 'selection_box': {'left_top': {'y': -61, 'x': -66}, 'right_bottom': {'y': -60, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -61.5, 'selection_box': {'left_top': {'y': -62, 'x': -66}, 'right_bottom': {'y': -61, 'x': -65}}}, {'machine_name': 'medium-electric-pole', 'x': -45.5, 'y': -60.5, 'selection_box': {'left_top': {'y': -61, 'x': -46}, 'right_bottom': {'y': -60, 'x': -45}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -58.5, 'selection_box': {'left_top': {'y': -59, 'x': -66}, 'right_bottom': {'y': -58, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -59.5, 'selection_box': {'left_top': {'y': -60, 'x': -66}, 'right_bottom': {'y': -59, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -56.5, 'selection_box': {'left_top': {'y': -57, 'x': -66}, 'right_bottom': {'y': -56, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -57.5, 'selection_box': {'left_top': {'y': -58, 'x': -66}, 'right_bottom': {'y': -57, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -49.5, 'y': -57.5, 'selection_box': {'left_top': {'y': -58, 'x': -50}, 'right_bottom': {'y': -57, 'x': -49}}}, {'machine_name': 'transport-belt', 'x': -49.5, 'y': -56.5, 'selection_box': {'left_top': {'y': -57, 'x': -50}, 'right_bottom': {'y': -56, 'x': -49}}}, {'machine_name': 'transport-belt', 'x': -46.5, 'y': -57.5, 'selection_box': {'left_top': {'y': -58, 'x': -47}, 'right_bottom': {'y': -57, 'x': -46}}}, {'machine_name': 'transport-belt', 'x': -46.5, 'y': -56.5, 'selection_box': {'left_top': {'y': -57, 'x': -47}, 'right_bottom': {'y': -56, 'x': -46}}}, {'machine_name': 'transport-belt', 'x': -44.5, 'y': -57.5, 'selection_box': {'left_top': {'y': -58, 'x': -45}, 'right_bottom': {'y': -57, 'x': -44}}}, {'machine_name': 'transport-belt', 'x': -45.5, 'y': -57.5, 'selection_box': {'left_top': {'y': -58, 'x': -46}, 'right_bottom': {'y': -57, 'x': -45}}}, {'machine_name': 'transport-belt', 'x': -43.5, 'y': -57.5, 'selection_box': {'left_top': {'y': -58, 'x': -44}, 'right_bottom': {'y': -57, 'x': -43}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -54.5, 'selection_box': {'left_top': {'y': -55, 'x': -66}, 'right_bottom': {'y': -54, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -55.5, 'selection_box': {'left_top': {'y': -56, 'x': -66}, 'right_bottom': {'y': -55, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -49.5, 'y': -55.5, 'selection_box': {'left_top': {'y': -56, 'x': -50}, 'right_bottom': {'y': -55, 'x': -49}}}, {'machine_name': 'transport-belt', 'x': -49.5, 'y': -54.5, 'selection_box': {'left_top': {'y': -55, 'x': -50}, 'right_bottom': {'y': -54, 'x': -49}}}, {'machine_name': 'transport-belt', 'x': -48.5, 'y': -54.5, 'selection_box': {'left_top': {'y': -55, 'x': -49}, 'right_bottom': {'y': -54, 'x': -48}}}, {'machine_name': 'transport-belt', 'x': -46.5, 'y': -54.5, 'selection_box': {'left_top': {'y': -55, 'x': -47}, 'right_bottom': {'y': -54, 'x': -46}}}, {'machine_name': 'transport-belt', 'x': -47.5, 'y': -54.5, 'selection_box': {'left_top': {'y': -55, 'x': -48}, 'right_bottom': {'y': -54, 'x': -47}}}, {'machine_name': 'transport-belt', 'x': -46.5, 'y': -55.5, 'selection_box': {'left_top': {'y': -56, 'x': -47}, 'right_bottom': {'y': -55, 'x': -46}}}, {'machine_name': 'transport-belt', 'x': -44.5, 'y': -54.5, 'selection_box': {'left_top': {'y': -55, 'x': -45}, 'right_bottom': {'y': -54, 'x': -44}}}, {'machine_name': 'transport-belt', 'x': -45.5, 'y': -54.5, 'selection_box': {'left_top': {'y': -55, 'x': -46}, 'right_bottom': {'y': -54, 'x': -45}}}, {'machine_name': 'transport-belt', 'x': -43.5, 'y': -54.5, 'selection_box': {'left_top': {'y': -55, 'x': -44}, 'right_bottom': {'y': -54, 'x': -43}}}, {'machine_name': 'medium-electric-pole', 'x': -39.5, 'y': -54.5, 'selection_box': {'left_top': {'y': -55, 'x': -40}, 'right_bottom': {'y': -54, 'x': -39}}}, {'machine_name': 'medium-electric-pole', 'x': -74.5, 'y': -53.5, 'selection_box': {'left_top': {'y': -54, 'x': -75}, 'right_bottom': {'y': -53, 'x': -74}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -52.5, 'selection_box': {'left_top': {'y': -53, 'x': -66}, 'right_bottom': {'y': -52, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -53.5, 'selection_box': {'left_top': {'y': -54, 'x': -66}, 'right_bottom': {'y': -53, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -46.5, 'y': -52.5, 'selection_box': {'left_top': {'y': -53, 'x': -47}, 'right_bottom': {'y': -52, 'x': -46}}}, {'machine_name': 'transport-belt', 'x': -46.5, 'y': -53.5, 'selection_box': {'left_top': {'y': -54, 'x': -47}, 'right_bottom': {'y': -53, 'x': -46}}}, {'machine_name': 'transport-belt', 'x': -43.5, 'y': -52.5, 'selection_box': {'left_top': {'y': -53, 'x': -44}, 'right_bottom': {'y': -52, 'x': -43}}}, {'machine_name': 'transport-belt', 'x': -43.5, 'y': -53.5, 'selection_box': {'left_top': {'y': -54, 'x': -44}, 'right_bottom': {'y': -53, 'x': -43}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -50.5, 'selection_box': {'left_top': {'y': -51, 'x': -66}, 'right_bottom': {'y': -50, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -51.5, 'selection_box': {'left_top': {'y': -52, 'x': -66}, 'right_bottom': {'y': -51, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -49.5, 'y': -51.5, 'selection_box': {'left_top': {'y': -52, 'x': -50}, 'right_bottom': {'y': -51, 'x': -49}}}, {'machine_name': 'transport-belt', 'x': -48.5, 'y': -51.5, 'selection_box': {'left_top': {'y': -52, 'x': -49}, 'right_bottom': {'y': -51, 'x': -48}}}, {'machine_name': 'transport-belt', 'x': -47.5, 'y': -51.5, 'selection_box': {'left_top': {'y': -52, 'x': -48}, 'right_bottom': {'y': -51, 'x': -47}}}, {'machine_name': 'transport-belt', 'x': -46.5, 'y': -51.5, 'selection_box': {'left_top': {'y': -52, 'x': -47}, 'right_bottom': {'y': -51, 'x': -46}}}, {'machine_name': 'transport-belt', 'x': -43.5, 'y': -51.5, 'selection_box': {'left_top': {'y': -52, 'x': -44}, 'right_bottom': {'y': -51, 'x': -43}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -48.5, 'selection_box': {'left_top': {'y': -49, 'x': -66}, 'right_bottom': {'y': -48, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -49.5, 'selection_box': {'left_top': {'y': -50, 'x': -66}, 'right_bottom': {'y': -49, 'x': -65}}}, {'machine_name': 'medium-electric-pole', 'x': -33.5, 'y': -48.5, 'selection_box': {'left_top': {'y': -49, 'x': -34}, 'right_bottom': {'y': -48, 'x': -33}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -46.5, 'selection_box': {'left_top': {'y': -47, 'x': -66}, 'right_bottom': {'y': -46, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -66}, 'right_bottom': {'y': -47, 'x': -65}}}, {'machine_name': 'medium-electric-pole', 'x': -62.5, 'y': -46.5, 'selection_box': {'left_top': {'y': -47, 'x': -63}, 'right_bottom': {'y': -46, 'x': -62}}}, {'machine_name': 'transport-belt', 'x': -60.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -61}, 'right_bottom': {'y': -47, 'x': -60}}}, {'machine_name': 'inserter', 'x': -60.5, 'y': -46.5, 'selection_box': {'left_top': {'y': -46.94921875, 'x': -60.8984375}, 'right_bottom': {'y': -46.15234375, 'x': -60.1015625}}}, {'machine_name': 'transport-belt', 'x': -58.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -59}, 'right_bottom': {'y': -47, 'x': -58}}}, {'machine_name': 'transport-belt', 'x': -59.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -60}, 'right_bottom': {'y': -47, 'x': -59}}}, {'machine_name': 'medium-electric-pole', 'x': -56.5, 'y': -46.5, 'selection_box': {'left_top': {'y': -47, 'x': -57}, 'right_bottom': {'y': -46, 'x': -56}}}, {'machine_name': 'transport-belt', 'x': -56.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -57}, 'right_bottom': {'y': -47, 'x': -56}}}, {'machine_name': 'transport-belt', 'x': -57.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -58}, 'right_bottom': {'y': -47, 'x': -57}}}, {'machine_name': 'inserter', 'x': -57.5, 'y': -46.5, 'selection_box': {'left_top': {'y': -46.94921875, 'x': -57.8984375}, 'right_bottom': {'y': -46.15234375, 'x': -57.1015625}}}, {'machine_name': 'transport-belt', 'x': -54.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -55}, 'right_bottom': {'y': -47, 'x': -54}}}, {'machine_name': 'transport-belt', 'x': -55.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -56}, 'right_bottom': {'y': -47, 'x': -55}}}, {'machine_name': 'inserter', 'x': -54.5, 'y': -46.5, 'selection_box': {'left_top': {'y': -46.94921875, 'x': -54.8984375}, 'right_bottom': {'y': -46.15234375, 'x': -54.1015625}}}, {'machine_name': 'transport-belt', 'x': -52.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -53}, 'right_bottom': {'y': -47, 'x': -52}}}, {'machine_name': 'transport-belt', 'x': -53.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -54}, 'right_bottom': {'y': -47, 'x': -53}}}, {'machine_name': 'transport-belt', 'x': -50.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -51}, 'right_bottom': {'y': -47, 'x': -50}}}, {'machine_name': 'medium-electric-pole', 'x': -50.5, 'y': -46.5, 'selection_box': {'left_top': {'y': -47, 'x': -51}, 'right_bottom': {'y': -46, 'x': -50}}}, {'machine_name': 'transport-belt', 'x': -51.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -52}, 'right_bottom': {'y': -47, 'x': -51}}}, {'machine_name': 'inserter', 'x': -51.5, 'y': -46.5, 'selection_box': {'left_top': {'y': -46.94921875, 'x': -51.8984375}, 'right_bottom': {'y': -46.15234375, 'x': -51.1015625}}}, {'machine_name': 'transport-belt', 'x': -48.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -49}, 'right_bottom': {'y': -47, 'x': -48}}}, {'machine_name': 'transport-belt', 'x': -49.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -50}, 'right_bottom': {'y': -47, 'x': -49}}}, {'machine_name': 'transport-belt', 'x': -46.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -47}, 'right_bottom': {'y': -47, 'x': -46}}}, {'machine_name': 'transport-belt', 'x': -47.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -48}, 'right_bottom': {'y': -47, 'x': -47}}}, {'machine_name': 'transport-belt', 'x': -44.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -45}, 'right_bottom': {'y': -47, 'x': -44}}}, {'machine_name': 'transport-belt', 'x': -45.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -46}, 'right_bottom': {'y': -47, 'x': -45}}}, {'machine_name': 'transport-belt', 'x': -42.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -43}, 'right_bottom': {'y': -47, 'x': -42}}}, {'machine_name': 'transport-belt', 'x': -43.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -44}, 'right_bottom': {'y': -47, 'x': -43}}}, {'machine_name': 'transport-belt', 'x': -41.5, 'y': -46.5, 'selection_box': {'left_top': {'y': -47, 'x': -42}, 'right_bottom': {'y': -46, 'x': -41}}}, {'machine_name': 'transport-belt', 'x': -41.5, 'y': -47.5, 'selection_box': {'left_top': {'y': -48, 'x': -42}, 'right_bottom': {'y': -47, 'x': -41}}}, {'machine_name': 'medium-electric-pole', 'x': -75.5, 'y': -45.5, 'selection_box': {'left_top': {'y': -46, 'x': -76}, 'right_bottom': {'y': -45, 'x': -75}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -45.5, 'selection_box': {'left_top': {'y': -46, 'x': -66}, 'right_bottom': {'y': -45, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -44.5, 'selection_box': {'left_top': {'y': -45, 'x': -66}, 'right_bottom': {'y': -44, 'x': -65}}}, {'machine_name': 'electric-furnace', 'x': -61.5, 'y': -44.5, 'selection_box': {'left_top': {'y': -46, 'x': -63}, 'right_bottom': {'y': -43, 'x': -60}}}, {'machine_name': 'electric-furnace', 'x': -58.5, 'y': -44.5, 'selection_box': {'left_top': {'y': -46, 'x': -60}, 'right_bottom': {'y': -43, 'x': -57}}}, {'machine_name': 'electric-furnace', 'x': -55.5, 'y': -44.5, 'selection_box': {'left_top': {'y': -46, 'x': -57}, 'right_bottom': {'y': -43, 'x': -54}}}, {'machine_name': 'electric-furnace', 'x': -52.5, 'y': -44.5, 'selection_box': {'left_top': {'y': -46, 'x': -54}, 'right_bottom': {'y': -43, 'x': -51}}}, {'machine_name': 'transport-belt', 'x': -41.5, 'y': -44.5, 'selection_box': {'left_top': {'y': -45, 'x': -42}, 'right_bottom': {'y': -44, 'x': -41}}}, {'machine_name': 'transport-belt', 'x': -41.5, 'y': -45.5, 'selection_box': {'left_top': {'y': -46, 'x': -42}, 'right_bottom': {'y': -45, 'x': -41}}}, {'machine_name': 'electric-mining-drill', 'x': -73.5, 'y': -42.5, 'selection_box': {'left_top': {'y': -44, 'x': -75}, 'right_bottom': {'y': -41, 'x': -72}}}, {'machine_name': 'transport-belt', 'x': -71.5, 'y': -42.5, 'selection_box': {'left_top': {'y': -43, 'x': -72}, 'right_bottom': {'y': -42, 'x': -71}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -42.5, 'selection_box': {'left_top': {'y': -43, 'x': -66}, 'right_bottom': {'y': -42, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -43.5, 'selection_box': {'left_top': {'y': -44, 'x': -66}, 'right_bottom': {'y': -43, 'x': -65}}}, {'machine_name': 'medium-electric-pole', 'x': -62.5, 'y': -42.5, 'selection_box': {'left_top': {'y': -43, 'x': -63}, 'right_bottom': {'y': -42, 'x': -62}}}, {'machine_name': 'inserter', 'x': -60.5, 'y': -42.5, 'selection_box': {'left_top': {'y': -42.94921875, 'x': -60.8984375}, 'right_bottom': {'y': -42.15234375, 'x': -60.1015625}}}, {'machine_name': 'medium-electric-pole', 'x': -56.5, 'y': -42.5, 'selection_box': {'left_top': {'y': -43, 'x': -57}, 'right_bottom': {'y': -42, 'x': -56}}}, {'machine_name': 'inserter', 'x': -57.5, 'y': -42.5, 'selection_box': {'left_top': {'y': -42.94921875, 'x': -57.8984375}, 'right_bottom': {'y': -42.15234375, 'x': -57.1015625}}}, {'machine_name': 'inserter', 'x': -54.5, 'y': -42.5, 'selection_box': {'left_top': {'y': -42.94921875, 'x': -54.8984375}, 'right_bottom': {'y': -42.15234375, 'x': -54.1015625}}}, {'machine_name': 'medium-electric-pole', 'x': -50.5, 'y': -42.5, 'selection_box': {'left_top': {'y': -43, 'x': -51}, 'right_bottom': {'y': -42, 'x': -50}}}, {'machine_name': 'inserter', 'x': -51.5, 'y': -42.5, 'selection_box': {'left_top': {'y': -42.94921875, 'x': -51.8984375}, 'right_bottom': {'y': -42.15234375, 'x': -51.1015625}}}, {'machine_name': 'inserter', 'x': -41.5, 'y': -43.5, 'selection_box': {'left_top': {'y': -43.84765625, 'x': -41.8984375}, 'right_bottom': {'y': -43.05078125, 'x': -41.1015625}}}, {'machine_name': 'inserter', 'x': -40.5, 'y': -42.5, 'selection_box': {'left_top': {'y': -42.8984375, 'x': -40.84765625}, 'right_bottom': {'y': -42.1015625, 'x': -40.05078125}}}, {'machine_name': 'medium-electric-pole', 'x': -39.5, 'y': -43.5, 'selection_box': {'left_top': {'y': -44, 'x': -40}, 'right_bottom': {'y': -43, 'x': -39}}}, {'machine_name': 'medium-electric-pole', 'x': -27.5, 'y': -42.5, 'selection_box': {'left_top': {'y': -43, 'x': -28}, 'right_bottom': {'y': -42, 'x': -27}}}, {'machine_name': 'medium-electric-pole', 'x': -75.5, 'y': -40.5, 'selection_box': {'left_top': {'y': -41, 'x': -76}, 'right_bottom': {'y': -40, 'x': -75}}}, {'machine_name': 'transport-belt', 'x': -70.5, 'y': -40.5, 'selection_box': {'left_top': {'y': -41, 'x': -71}, 'right_bottom': {'y': -40, 'x': -70}}}, {'machine_name': 'transport-belt', 'x': -71.5, 'y': -40.5, 'selection_box': {'left_top': {'y': -41, 'x': -72}, 'right_bottom': {'y': -40, 'x': -71}}}, {'machine_name': 'transport-belt', 'x': -71.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -72}, 'right_bottom': {'y': -41, 'x': -71}}}, {'machine_name': 'transport-belt', 'x': -68.5, 'y': -40.5, 'selection_box': {'left_top': {'y': -41, 'x': -69}, 'right_bottom': {'y': -40, 'x': -68}}}, {'machine_name': 'transport-belt', 'x': -69.5, 'y': -40.5, 'selection_box': {'left_top': {'y': -41, 'x': -70}, 'right_bottom': {'y': -40, 'x': -69}}}, {'machine_name': 'transport-belt', 'x': -66.5, 'y': -40.5, 'selection_box': {'left_top': {'y': -41, 'x': -67}, 'right_bottom': {'y': -40, 'x': -66}}}, {'machine_name': 'transport-belt', 'x': -67.5, 'y': -40.5, 'selection_box': {'left_top': {'y': -41, 'x': -68}, 'right_bottom': {'y': -40, 'x': -67}}}, {'machine_name': 'transport-belt', 'x': -64.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -65}, 'right_bottom': {'y': -41, 'x': -64}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -66}, 'right_bottom': {'y': -41, 'x': -65}}}, {'machine_name': 'transport-belt', 'x': -62.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -63}, 'right_bottom': {'y': -41, 'x': -62}}}, {'machine_name': 'transport-belt', 'x': -63.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -64}, 'right_bottom': {'y': -41, 'x': -63}}}, {'machine_name': 'transport-belt', 'x': -60.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -61}, 'right_bottom': {'y': -41, 'x': -60}}}, {'machine_name': 'transport-belt', 'x': -61.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -62}, 'right_bottom': {'y': -41, 'x': -61}}}, {'machine_name': 'transport-belt', 'x': -58.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -59}, 'right_bottom': {'y': -41, 'x': -58}}}, {'machine_name': 'transport-belt', 'x': -59.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -60}, 'right_bottom': {'y': -41, 'x': -59}}}, {'machine_name': 'transport-belt', 'x': -56.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -57}, 'right_bottom': {'y': -41, 'x': -56}}}, {'machine_name': 'transport-belt', 'x': -57.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -58}, 'right_bottom': {'y': -41, 'x': -57}}}, {'machine_name': 'transport-belt', 'x': -54.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -55}, 'right_bottom': {'y': -41, 'x': -54}}}, {'machine_name': 'transport-belt', 'x': -55.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -56}, 'right_bottom': {'y': -41, 'x': -55}}}, {'machine_name': 'transport-belt', 'x': -52.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -53}, 'right_bottom': {'y': -41, 'x': -52}}}, {'machine_name': 'transport-belt', 'x': -53.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -54}, 'right_bottom': {'y': -41, 'x': -53}}}, {'machine_name': 'transport-belt', 'x': -51.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -52}, 'right_bottom': {'y': -41, 'x': -51}}}, {'machine_name': 'medium-electric-pole', 'x': -46.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -42, 'x': -47}, 'right_bottom': {'y': -41, 'x': -46}}}, {'machine_name': 'assembling-machine-1', 'x': -42.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -43, 'x': -44}, 'right_bottom': {'y': -40, 'x': -41}}}, {'machine_name': 'assembling-machine-1', 'x': -38.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -43, 'x': -40}, 'right_bottom': {'y': -40, 'x': -37}}}, {'machine_name': 'inserter', 'x': -36.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -41.8984375, 'x': -36.84765625}, 'right_bottom': {'y': -41.1015625, 'x': -36.05078125}}}, {'machine_name': 'lab', 'x': -34.5, 'y': -41.5, 'selection_box': {'left_top': {'y': -43, 'x': -36}, 'right_bottom': {'y': -40, 'x': -33}}}, {'machine_name': 'electric-mining-drill', 'x': -73.5, 'y': -39.5, 'selection_box': {'left_top': {'y': -41, 'x': -75}, 'right_bottom': {'y': -38, 'x': -72}}}, {'machine_name': 'transport-belt', 'x': -71.5, 'y': -39.5, 'selection_box': {'left_top': {'y': -40, 'x': -72}, 'right_bottom': {'y': -39, 'x': -71}}}, {'machine_name': 'transport-belt', 'x': -66.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -67}, 'right_bottom': {'y': -38, 'x': -66}}}, {'machine_name': 'transport-belt', 'x': -66.5, 'y': -39.5, 'selection_box': {'left_top': {'y': -40, 'x': -67}, 'right_bottom': {'y': -39, 'x': -66}}}, {'machine_name': 'transport-belt', 'x': -60.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -61}, 'right_bottom': {'y': -38, 'x': -60}}}, {'machine_name': 'transport-belt', 'x': -58.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -59}, 'right_bottom': {'y': -38, 'x': -58}}}, {'machine_name': 'transport-belt', 'x': -59.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -60}, 'right_bottom': {'y': -38, 'x': -59}}}, {'machine_name': 'transport-belt', 'x': -56.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -57}, 'right_bottom': {'y': -38, 'x': -56}}}, {'machine_name': 'transport-belt', 'x': -57.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -58}, 'right_bottom': {'y': -38, 'x': -57}}}, {'machine_name': 'transport-belt', 'x': -54.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -55}, 'right_bottom': {'y': -38, 'x': -54}}}, {'machine_name': 'transport-belt', 'x': -55.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -56}, 'right_bottom': {'y': -38, 'x': -55}}}, {'machine_name': 'transport-belt', 'x': -52.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -53}, 'right_bottom': {'y': -38, 'x': -52}}}, {'machine_name': 'transport-belt', 'x': -53.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -54}, 'right_bottom': {'y': -38, 'x': -53}}}, {'machine_name': 'transport-belt', 'x': -50.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -51}, 'right_bottom': {'y': -38, 'x': -50}}}, {'machine_name': 'transport-belt', 'x': -51.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -52}, 'right_bottom': {'y': -38, 'x': -51}}}, {'machine_name': 'transport-belt', 'x': -48.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -49}, 'right_bottom': {'y': -38, 'x': -48}}}, {'machine_name': 'transport-belt', 'x': -49.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -50}, 'right_bottom': {'y': -38, 'x': -49}}}, {'machine_name': 'transport-belt', 'x': -47.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -48}, 'right_bottom': {'y': -38, 'x': -47}}}, {'machine_name': 'transport-belt', 'x': -46.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -47}, 'right_bottom': {'y': -38, 'x': -46}}}, {'machine_name': 'transport-belt', 'x': -44.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -45}, 'right_bottom': {'y': -38, 'x': -44}}}, {'machine_name': 'transport-belt', 'x': -45.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -46}, 'right_bottom': {'y': -38, 'x': -45}}}, {'machine_name': 'transport-belt', 'x': -42.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -43}, 'right_bottom': {'y': -38, 'x': -42}}}, {'machine_name': 'transport-belt', 'x': -43.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -44}, 'right_bottom': {'y': -38, 'x': -43}}}, {'machine_name': 'transport-belt', 'x': -40.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -41}, 'right_bottom': {'y': -38, 'x': -40}}}, {'machine_name': 'transport-belt', 'x': -41.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -42}, 'right_bottom': {'y': -38, 'x': -41}}}, {'machine_name': 'inserter', 'x': -39.5, 'y': -39.5, 'selection_box': {'left_top': {'y': -39.94921875, 'x': -39.8984375}, 'right_bottom': {'y': -39.15234375, 'x': -39.1015625}}}, {'machine_name': 'transport-belt', 'x': -39.5, 'y': -38.5, 'selection_box': {'left_top': {'y': -39, 'x': -40}, 'right_bottom': {'y': -38, 'x': -39}}}, {'machine_name': 'medium-electric-pole', 'x': -36.5, 'y': -39.5, 'selection_box': {'left_top': {'y': -40, 'x': -37}, 'right_bottom': {'y': -39, 'x': -36}}}, {'machine_name': 'medium-electric-pole', 'x': -67.5, 'y': -37.5, 'selection_box': {'left_top': {'y': -38, 'x': -68}, 'right_bottom': {'y': -37, 'x': -67}}}, {'machine_name': 'transport-belt', 'x': -66.5, 'y': -36.5, 'selection_box': {'left_top': {'y': -37, 'x': -67}, 'right_bottom': {'y': -36, 'x': -66}}}, {'machine_name': 'transport-belt', 'x': -66.5, 'y': -37.5, 'selection_box': {'left_top': {'y': -38, 'x': -67}, 'right_bottom': {'y': -37, 'x': -66}}}, {'machine_name': 'medium-electric-pole', 'x': -62.5, 'y': -37.5, 'selection_box': {'left_top': {'y': -38, 'x': -63}, 'right_bottom': {'y': -37, 'x': -62}}}, {'machine_name': 'inserter', 'x': -60.5, 'y': -37.5, 'selection_box': {'left_top': {'y': -37.94921875, 'x': -60.8984375}, 'right_bottom': {'y': -37.15234375, 'x': -60.1015625}}}, {'machine_name': 'medium-electric-pole', 'x': -56.5, 'y': -37.5, 'selection_box': {'left_top': {'y': -38, 'x': -57}, 'right_bottom': {'y': -37, 'x': -56}}}, {'machine_name': 'inserter', 'x': -57.5, 'y': -37.5, 'selection_box': {'left_top': {'y': -37.94921875, 'x': -57.8984375}, 'right_bottom': {'y': -37.15234375, 'x': -57.1015625}}}, {'machine_name': 'inserter', 'x': -54.5, 'y': -37.5, 'selection_box': {'left_top': {'y': -37.94921875, 'x': -54.8984375}, 'right_bottom': {'y': -37.15234375, 'x': -54.1015625}}}, {'machine_name': 'medium-electric-pole', 'x': -50.5, 'y': -37.5, 'selection_box': {'left_top': {'y': -38, 'x': -51}, 'right_bottom': {'y': -37, 'x': -50}}}, {'machine_name': 'inserter', 'x': -51.5, 'y': -37.5, 'selection_box': {'left_top': {'y': -37.94921875, 'x': -51.8984375}, 'right_bottom': {'y': -37.15234375, 'x': -51.1015625}}}, {'machine_name': 'medium-electric-pole', 'x': -21.5, 'y': -36.5, 'selection_box': {'left_top': {'y': -37, 'x': -22}, 'right_bottom': {'y': -36, 'x': -21}}}, {'machine_name': 'transport-belt', 'x': -66.5, 'y': -34.5, 'selection_box': {'left_top': {'y': -35, 'x': -67}, 'right_bottom': {'y': -34, 'x': -66}}}, {'machine_name': 'transport-belt', 'x': -66.5, 'y': -35.5, 'selection_box': {'left_top': {'y': -36, 'x': -67}, 'right_bottom': {'y': -35, 'x': -66}}}, {'machine_name': 'electric-furnace', 'x': -61.5, 'y': -35.5, 'selection_box': {'left_top': {'y': -37, 'x': -63}, 'right_bottom': {'y': -34, 'x': -60}}}, {'machine_name': 'electric-furnace', 'x': -58.5, 'y': -35.5, 'selection_box': {'left_top': {'y': -37, 'x': -60}, 'right_bottom': {'y': -34, 'x': -57}}}, {'machine_name': 'electric-furnace', 'x': -55.5, 'y': -35.5, 'selection_box': {'left_top': {'y': -37, 'x': -57}, 'right_bottom': {'y': -34, 'x': -54}}}, {'machine_name': 'electric-furnace', 'x': -52.5, 'y': -35.5, 'selection_box': {'left_top': {'y': -37, 'x': -54}, 'right_bottom': {'y': -34, 'x': -51}}}, {'machine_name': 'transport-belt', 'x': -66.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -67}, 'right_bottom': {'y': -32, 'x': -66}}}, {'machine_name': 'transport-belt', 'x': -66.5, 'y': -33.5, 'selection_box': {'left_top': {'y': -34, 'x': -67}, 'right_bottom': {'y': -33, 'x': -66}}}, {'machine_name': 'transport-belt', 'x': -64.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -65}, 'right_bottom': {'y': -32, 'x': -64}}}, {'machine_name': 'transport-belt', 'x': -65.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -66}, 'right_bottom': {'y': -32, 'x': -65}}}, {'machine_name': 'medium-electric-pole', 'x': -62.5, 'y': -33.5, 'selection_box': {'left_top': {'y': -34, 'x': -63}, 'right_bottom': {'y': -33, 'x': -62}}}, {'machine_name': 'transport-belt', 'x': -62.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -63}, 'right_bottom': {'y': -32, 'x': -62}}}, {'machine_name': 'transport-belt', 'x': -63.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -64}, 'right_bottom': {'y': -32, 'x': -63}}}, {'machine_name': 'transport-belt', 'x': -60.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -61}, 'right_bottom': {'y': -32, 'x': -60}}}, {'machine_name': 'transport-belt', 'x': -61.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -62}, 'right_bottom': {'y': -32, 'x': -61}}}, {'machine_name': 'inserter', 'x': -60.5, 'y': -33.5, 'selection_box': {'left_top': {'y': -33.94921875, 'x': -60.8984375}, 'right_bottom': {'y': -33.15234375, 'x': -60.1015625}}}, {'machine_name': 'transport-belt', 'x': -58.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -59}, 'right_bottom': {'y': -32, 'x': -58}}}, {'machine_name': 'transport-belt', 'x': -59.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -60}, 'right_bottom': {'y': -32, 'x': -59}}}, {'machine_name': 'medium-electric-pole', 'x': -56.5, 'y': -33.5, 'selection_box': {'left_top': {'y': -34, 'x': -57}, 'right_bottom': {'y': -33, 'x': -56}}}, {'machine_name': 'inserter', 'x': -57.5, 'y': -33.5, 'selection_box': {'left_top': {'y': -33.94921875, 'x': -57.8984375}, 'right_bottom': {'y': -33.15234375, 'x': -57.1015625}}}, {'machine_name': 'transport-belt', 'x': -56.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -57}, 'right_bottom': {'y': -32, 'x': -56}}}, {'machine_name': 'transport-belt', 'x': -57.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -58}, 'right_bottom': {'y': -32, 'x': -57}}}, {'machine_name': 'inserter', 'x': -54.5, 'y': -33.5, 'selection_box': {'left_top': {'y': -33.94921875, 'x': -54.8984375}, 'right_bottom': {'y': -33.15234375, 'x': -54.1015625}}}, {'machine_name': 'transport-belt', 'x': -54.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -55}, 'right_bottom': {'y': -32, 'x': -54}}}, {'machine_name': 'transport-belt', 'x': -55.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -56}, 'right_bottom': {'y': -32, 'x': -55}}}, {'machine_name': 'transport-belt', 'x': -52.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -53}, 'right_bottom': {'y': -32, 'x': -52}}}, {'machine_name': 'transport-belt', 'x': -53.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -54}, 'right_bottom': {'y': -32, 'x': -53}}}, {'machine_name': 'medium-electric-pole', 'x': -50.5, 'y': -33.5, 'selection_box': {'left_top': {'y': -34, 'x': -51}, 'right_bottom': {'y': -33, 'x': -50}}}, {'machine_name': 'transport-belt', 'x': -51.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -52}, 'right_bottom': {'y': -32, 'x': -51}}}, {'machine_name': 'inserter', 'x': -51.5, 'y': -33.5, 'selection_box': {'left_top': {'y': -33.94921875, 'x': -51.8984375}, 'right_bottom': {'y': -33.15234375, 'x': -51.1015625}}}, {'machine_name': 'medium-electric-pole', 'x': -13.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -14}, 'right_bottom': {'y': -32, 'x': -13}}}, {'machine_name': 'medium-electric-pole', 'x': -4.5, 'y': -32.5, 'selection_box': {'left_top': {'y': -33, 'x': -5}, 'right_bottom': {'y': -32, 'x': -4}}}, {'machine_name': 'transport-belt', 'x': -28.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': -29}, 'right_bottom': {'y': -26, 'x': -28}}}, {'machine_name': 'express-transport-belt', 'x': -26.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': -27}, 'right_bottom': {'y': -26, 'x': -26}}}, {'machine_name': 'fast-transport-belt', 'x': -27.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': -28}, 'right_bottom': {'y': -26, 'x': -27}}}, {'machine_name': 'turbo-transport-belt', 'x': -25.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': -26}, 'right_bottom': {'y': -26, 'x': -25}}}, {'machine_name': 'inserter', 'x': -20.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -26.84765625, 'x': -20.8984375}, 'right_bottom': {'y': -26.05078125, 'x': -20.1015625}}}, {'machine_name': 'burner-inserter', 'x': -21.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -26.84765625, 'x': -21.8984375}, 'right_bottom': {'y': -26.05078125, 'x': -21.1015625}}}, {'machine_name': 'steam-engine', 'x': -16.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -29, 'x': -18}, 'right_bottom': {'y': -24, 'x': -15}}}, {'machine_name': 'offshore-pump', 'x': -5.5, 'y': -27.5, 'selection_box': {'left_top': {'y': -27.98828125, 'x': -6.09765625}, 'right_bottom': {'y': -26.01171875, 'x': -4.90234375}}}, {'machine_name': 'pipe', 'x': -3.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': -4}, 'right_bottom': {'y': -26, 'x': -3}}}, {'machine_name': 'small-electric-pole', 'x': -0.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -26.8984375, 'x': -0.8984375}, 'right_bottom': {'y': -26.1015625, 'x': -0.1015625}}}, {'machine_name': 'pipe-to-ground', 'x': -1.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': -2}, 'right_bottom': {'y': -26, 'x': -1}}}, {'machine_name': 'medium-electric-pole', 'x': 0.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': 0}, 'right_bottom': {'y': -26, 'x': 1}}}, {'machine_name': 'assembling-machine-1', 'x': -46.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -48}, 'right_bottom': {'y': -24, 'x': -45}}}, {'machine_name': 'assembling-machine-2', 'x': -43.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -45}, 'right_bottom': {'y': -24, 'x': -42}}}, {'machine_name': 'assembling-machine-3', 'x': -40.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -42}, 'right_bottom': {'y': -24, 'x': -39}}}, {'machine_name': 'stone-furnace', 'x': -38, 'y': -26, 'selection_box': {'left_top': {'y': -27, 'x': -38.796875}, 'right_bottom': {'y': -25, 'x': -37.203125}}}, {'machine_name': 'steel-furnace', 'x': -36, 'y': -26, 'selection_box': {'left_top': {'y': -27, 'x': -36.796875}, 'right_bottom': {'y': -25, 'x': -35.203125}}}, {'machine_name': 'burner-mining-drill', 'x': -34, 'y': -26, 'selection_box': {'left_top': {'y': -27, 'x': -35}, 'right_bottom': {'y': -25, 'x': -33}}}, {'machine_name': 'electric-mining-drill', 'x': -30.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -32}, 'right_bottom': {'y': -24, 'x': -29}}}, {'machine_name': 'underground-belt', 'x': -28.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -26, 'x': -29}, 'right_bottom': {'y': -25, 'x': -28}}}, {'machine_name': 'express-underground-belt', 'x': -26.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -26, 'x': -27}, 'right_bottom': {'y': -25, 'x': -26}}}, {'machine_name': 'fast-underground-belt', 'x': -27.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -26, 'x': -28}, 'right_bottom': {'y': -25, 'x': -27}}}, {'machine_name': 'turbo-underground-belt', 'x': -25.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -26, 'x': -26}, 'right_bottom': {'y': -25, 'x': -25}}}, {'machine_name': 'chemical-plant', 'x': -23.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -25}, 'right_bottom': {'y': -24, 'x': -22}}}, {'machine_name': 'bulk-inserter', 'x': -21.5, 'y': -24.5, 'selection_box': {'left_top': {'y': -24.84765625, 'x': -21.8984375}, 'right_bottom': {'y': -24.05078125, 'x': -21.1015625}}}, {'machine_name': 'fast-inserter', 'x': -20.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -25.84765625, 'x': -20.8984375}, 'right_bottom': {'y': -25.05078125, 'x': -20.1015625}}}, {'machine_name': 'long-handed-inserter', 'x': -21.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -25.84765625, 'x': -21.8984375}, 'right_bottom': {'y': -25.05078125, 'x': -21.1015625}}}, {'machine_name': 'boiler', 'x': -19, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -20}, 'right_bottom': {'y': -24, 'x': -18}}}, {'machine_name': 'oil-refinery', 'x': -12.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -28, 'x': -15}, 'right_bottom': {'y': -23, 'x': -10}}}, {'machine_name': 'pipe', 'x': -3.5, 'y': -24.5, 'selection_box': {'left_top': {'y': -25, 'x': -4}, 'right_bottom': {'y': -24, 'x': -3}}}, {'machine_name': 'pipe', 'x': -3.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -26, 'x': -4}, 'right_bottom': {'y': -25, 'x': -3}}}, {'machine_name': 'pipe-to-ground', 'x': -1.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -26, 'x': -2}, 'right_bottom': {'y': -25, 'x': -1}}}, {'machine_name': 'big-electric-pole', 'x': 2, 'y': -26, 'selection_box': {'left_top': {'y': -27, 'x': 1}, 'right_bottom': {'y': -25, 'x': 3}}}, {'machine_name': 'substation', 'x': 4, 'y': -26, 'selection_box': {'left_top': {'y': -27, 'x': 3}, 'right_bottom': {'y': -25, 'x': 5}}}, {'machine_name': 'pipe', 'x': -3.5, 'y': -23.5, 'selection_box': {'left_top': {'y': -24, 'x': -4}, 'right_bottom': {'y': -23, 'x': -3}}}]
     raw_entities_BB = [{'machine_name': 'transport-belt', 'x': -28.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': -29}, 'right_bottom': {'y': -26, 'x': -28}}, 'rotation': 12}, {'machine_name': 'express-transport-belt', 'x': -26.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': -27}, 'right_bottom': {'y': -26, 'x': -26}}, 'rotation': 12}, {'machine_name': 'fast-transport-belt', 'x': -27.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': -28}, 'right_bottom': {'y': -26, 'x': -27}}, 'rotation': 8}, {'machine_name': 'turbo-transport-belt', 'x': -25.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': -26}, 'right_bottom': {'y': -26, 'x': -25}}, 'rotation': 0}, {'machine_name': 'inserter', 'x': -20.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -26.84765625, 'x': -20.8984375}, 'right_bottom': {'y': -26.05078125, 'x': -20.1015625}}, 'rotation': 0}, {'machine_name': 'burner-inserter', 'x': -21.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -26.84765625, 'x': -21.8984375}, 'right_bottom': {'y': -26.05078125, 'x': -21.1015625}}, 'rotation': 0}, {'machine_name': 'steam-engine', 'x': -16.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -29, 'x': -18}, 'right_bottom': {'y': -24, 'x': -15}}, 'rotation': 0}, {'machine_name': 'offshore-pump', 'x': -5.5, 'y': -27.5, 'selection_box': {'left_top': {'y': -27.98828125, 'x': -6.09765625}, 'right_bottom': {'y': -26.01171875, 'x': -4.90234375}}, 'rotation': 8}, {'machine_name': 'pipe', 'x': -3.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': -4}, 'right_bottom': {'y': -26, 'x': -3}}, 'rotation': 0}, {'machine_name': 'small-electric-pole', 'x': -0.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -26.8984375, 'x': -0.8984375}, 'right_bottom': {'y': -26.1015625, 'x': -0.1015625}}, 'rotation': 0}, {'machine_name': 'pipe-to-ground', 'x': -1.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': -2}, 'right_bottom': {'y': -26, 'x': -1}}, 'rotation': 8}, {'machine_name': 'medium-electric-pole', 'x': 0.5, 'y': -26.5, 'selection_box': {'left_top': {'y': -27, 'x': 0}, 'right_bottom': {'y': -26, 'x': 1}}, 'rotation': 0}, {'machine_name': 'assembling-machine-1', 'x': -46.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -48}, 'right_bottom': {'y': -24, 'x': -45}}, 'rotation': 0}, {'machine_name': 'assembling-machine-2', 'x': -43.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -45}, 'right_bottom': {'y': -24, 'x': -42}}, 'rotation': 0}, {'machine_name': 'assembling-machine-3', 'x': -40.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -42}, 'right_bottom': {'y': -24, 'x': -39}}, 'rotation': 0}, {'machine_name': 'stone-furnace', 'x': -38, 'y': -26, 'selection_box': {'left_top': {'y': -27, 'x': -38.796875}, 'right_bottom': {'y': -25, 'x': -37.203125}}, 'rotation': 0}, {'machine_name': 'steel-furnace', 'x': -36, 'y': -26, 'selection_box': {'left_top': {'y': -27, 'x': -36.796875}, 'right_bottom': {'y': -25, 'x': -35.203125}}, 'rotation': 0}, {'machine_name': 'burner-mining-drill', 'x': -34, 'y': -26, 'selection_box': {'left_top': {'y': -27, 'x': -35}, 'right_bottom': {'y': -25, 'x': -33}}, 'rotation': 8}, {'machine_name': 'electric-mining-drill', 'x': -30.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -32}, 'right_bottom': {'y': -24, 'x': -29}}, 'rotation': 8}, {'machine_name': 'underground-belt', 'x': -28.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -26, 'x': -29}, 'right_bottom': {'y': -25, 'x': -28}}, 'rotation': 8}, {'machine_name': 'express-underground-belt', 'x': -26.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -26, 'x': -27}, 'right_bottom': {'y': -25, 'x': -26}}, 'rotation': 8}, {'machine_name': 'fast-underground-belt', 'x': -27.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -26, 'x': -28}, 'right_bottom': {'y': -25, 'x': -27}}, 'rotation': 8}, {'machine_name': 'turbo-underground-belt', 'x': -25.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -26, 'x': -26}, 'right_bottom': {'y': -25, 'x': -25}}, 'rotation': 0}, {'machine_name': 'chemical-plant', 'x': -23.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -25}, 'right_bottom': {'y': -24, 'x': -22}}, 'rotation': 8}, {'machine_name': 'bulk-inserter', 'x': -21.5, 'y': -24.5, 'selection_box': {'left_top': {'y': -24.84765625, 'x': -21.8984375}, 'right_bottom': {'y': -24.05078125, 'x': -21.1015625}}, 'rotation': 0}, {'machine_name': 'fast-inserter', 'x': -20.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -25.84765625, 'x': -20.8984375}, 'right_bottom': {'y': -25.05078125, 'x': -20.1015625}}, 'rotation': 0}, {'machine_name': 'long-handed-inserter', 'x': -21.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -25.84765625, 'x': -21.8984375}, 'right_bottom': {'y': -25.05078125, 'x': -21.1015625}}, 'rotation': 0}, {'machine_name': 'boiler', 'x': -19, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -20}, 'right_bottom': {'y': -24, 'x': -18}}, 'rotation': 12}, {'machine_name': 'oil-refinery', 'x': -12.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -28, 'x': -15}, 'right_bottom': {'y': -23, 'x': -10}}, 'rotation': 8}, {'machine_name': 'lab', 'x': -8.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -27, 'x': -10}, 'right_bottom': {'y': -24, 'x': -7}}, 'rotation': 0}, {'machine_name': 'pipe', 'x': -3.5, 'y': -24.5, 'selection_box': {'left_top': {'y': -25, 'x': -4}, 'right_bottom': {'y': -24, 'x': -3}}, 'rotation': 0}, {'machine_name': 'pipe', 'x': -3.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -26, 'x': -4}, 'right_bottom': {'y': -25, 'x': -3}}, 'rotation': 0}, {'machine_name': 'pipe-to-ground', 'x': -1.5, 'y': -25.5, 'selection_box': {'left_top': {'y': -26, 'x': -2}, 'right_bottom': {'y': -25, 'x': -1}}, 'rotation': 0}, {'machine_name': 'big-electric-pole', 'x': 2, 'y': -26, 'selection_box': {'left_top': {'y': -27, 'x': 1}, 'right_bottom': {'y': -25, 'x': 3}}, 'rotation': 0}, {'machine_name': 'substation', 'x': 4, 'y': -26, 'selection_box': {'left_top': {'y': -27, 'x': 3}, 'right_bottom': {'y': -25, 'x': 5}}, 'rotation': 0}]


machines = [{'machine_name': 'offshore-pump', 'x': -3.5, 'y': -25.5,
             'selection_box': {'left_top': {'y': -26.09765625, 'x': -4.98828125},
                               'right_bottom': {'y': -24.90234375, 'x': -3.01171875}}, 'rotation': 12},
            {'machine_name': 'pipe-to-ground', 'x': 20.5, 'y': -18.5,
             'selection_box': {'left_top': {'y': -19, 'x': 20}, 'right_bottom': {'y': -18, 'x': 21}}, 'rotation': 8},
            {'machine_name': 'pipe', 'x': -8.5, 'y': -17.5,
             'selection_box': {'left_top': {'y': -18, 'x': -9}, 'right_bottom': {'y': -17, 'x': -8}}, 'rotation': 0},
            {'machine_name': 'pipe', 'x': -8.5, 'y': -16.5,
             'selection_box': {'left_top': {'y': -17, 'x': -9}, 'right_bottom': {'y': -16, 'x': -8}}, 'rotation': 0},
            {'machine_name': 'pipe', 'x': -9.5, 'y': -16.5,
             'selection_box': {'left_top': {'y': -17, 'x': -10}, 'right_bottom': {'y': -16, 'x': -9}}, 'rotation': 0},
            {'machine_name': 'pipe', 'x': -7.5, 'y': -16.5,
             'selection_box': {'left_top': {'y': -17, 'x': -8}, 'right_bottom': {'y': -16, 'x': -7}}, 'rotation': 0},
            {'machine_name': 'pipe-to-ground', 'x': 18.5, 'y': -16.5,
             'selection_box': {'left_top': {'y': -17, 'x': 18}, 'right_bottom': {'y': -16, 'x': 19}}, 'rotation': 4},
            {'machine_name': 'boiler', 'x': 20.5, 'y': -17,
             'selection_box': {'left_top': {'y': -18, 'x': 19}, 'right_bottom': {'y': -16, 'x': 22}}, 'rotation': 0},
            {'machine_name': 'pipe', 'x': 22.5, 'y': -16.5,
             'selection_box': {'left_top': {'y': -17, 'x': 22}, 'right_bottom': {'y': -16, 'x': 23}}, 'rotation': 0},
            {'machine_name': 'pipe', 'x': -8.5, 'y': -14.5,
             'selection_box': {'left_top': {'y': -15, 'x': -9}, 'right_bottom': {'y': -14, 'x': -8}}, 'rotation': 0},
            {'machine_name': 'pipe', 'x': -8.5, 'y': -15.5,
             'selection_box': {'left_top': {'y': -16, 'x': -9}, 'right_bottom': {'y': -15, 'x': -8}}, 'rotation': 0}]


def get_search_coords(x, y, rotation, distance=1):
    """Return the coordinates at a certain distance in the direction of rotation."""
    if rotation == 0:
        return x, y - distance
    elif rotation == 4:
        return x + distance, y
    elif rotation == 8:
        return x, y + distance
    elif rotation == 12:
        return x - distance, y


def is_point_in_selection_box(px, py, selection_box):
    """Check if a point (px, py) is inside the selection box."""
    left_top = selection_box['left_top']
    right_bottom = selection_box['right_bottom']

    return (left_top['x'] <= px <= right_bottom['x'] and
            left_top['y'] <= py <= right_bottom['y'])


def find_edges(machine_list, check_from, check_to, max_distance=1, strict_rotation=False, check_selection_box=False,
               is_underground_belt=False, is_inserter=False, is_pipe_to_ground=False):
    """
    Generic edge detection.

    check_from: tuple/list of machine types to start from
    check_to: tuple/list of machine types to check edges to
    max_distance: how far to look in the direction of rotation
    strict_rotation: if True, only match exact rotation
    check_selection_box: if True, verify search coords are within target's selection box
    is_underground_belt: if True, use underground belt pairing logic (same rotation)
    is_inserter: if True, use inserter pickup/drop logic
    is_pipe_to_ground: if True, use pipe-to-ground pairing logic (opposite rotation)
    """
    edges = []

    # Handle inserter logic separately
    if is_inserter:
        all_machines = machine_list

        for machine in machine_list:
            if machine['machine_name'] not in check_from:
                continue

            x, y, rotation = machine['x'], machine['y'], machine['rotation']

            # Determine pickup/drop distance based on inserter type
            if machine['machine_name'] == 'long-handed-inserter':
                pickup_distance = 2
                drop_distance = 2
            else:
                pickup_distance = 1
                drop_distance = 1

            print(f"\n=== INSERTER ({machine['machine_name']}) at x: {x}, y: {y}, rotation: {rotation} ===")

            # Check tiles in front (pickup side)
            front_x, front_y = get_search_coords(x, y, rotation, distance=pickup_distance)
            print(f"  Front (pickup): x: {front_x}, y: {front_y} (distance: {pickup_distance})")

            # Check tiles behind (drop side) - opposite direction
            behind_rotation = (rotation + 8) % 16
            behind_x, behind_y = get_search_coords(x, y, behind_rotation, distance=drop_distance)
            print(f"  Behind (drop): x: {behind_x}, y: {behind_y} (distance: {drop_distance})")

            # Check all machines to see if front/behind coords are in their selection boxes
            front_entity = None
            behind_entity = None

            for other in all_machines:
                if other == machine:
                    continue

                # Check if it's an assembler or transport belt
                if not (other['machine_name'].startswith('assembling-machine') or
                        'transport-belt' in other['machine_name'] or
                        'belt' in other['machine_name']):
                    continue

                # Check front position
                if is_point_in_selection_box(front_x, front_y, other['selection_box']):
                    front_entity = other
                    print(f"    ✓ Front intersects {other['machine_name']} at ({other['x']}, {other['y']})")

                # Check behind position
                if is_point_in_selection_box(behind_x, behind_y, other['selection_box']):
                    behind_entity = other
                    print(f"    ✓ Behind intersects {other['machine_name']} at ({other['x']}, {other['y']})")

            # Create separate edges for pickup and drop
            if front_entity:
                edges.append({
                    "from_name": front_entity['machine_name'],
                    "from_x": front_entity['x'],
                    "from_y": front_entity['y'],
                    "to_name": machine['machine_name'],
                    "to_x": x,
                    "to_y": y
                })
                print(
                    f"  ➜ PICKUP EDGE: {front_entity['machine_name']}({front_entity['x']},{front_entity['y']}) -> {machine['machine_name']}({x},{y})")

            if behind_entity:
                edges.append({
                    "from_name": machine['machine_name'],
                    "from_x": x,
                    "from_y": y,
                    "to_name": behind_entity['machine_name'],
                    "to_x": behind_entity['x'],
                    "to_y": behind_entity['y']
                })
                print(
                    f"  ➜ DROP EDGE: {machine['machine_name']}({x},{y}) -> {behind_entity['machine_name']}({behind_entity['x']},{behind_entity['y']})")

        return edges

    # Handle pipe-to-ground pairing logic (opposite rotations, search in opposite direction)
    if is_pipe_to_ground:
        coord_lookup = {}
        for m in machine_list:
            coord_lookup[(m['x'], m['y'])] = m

        for machine in machine_list:
            if machine['machine_name'] not in check_from:
                continue

            x, y, rotation = machine['x'], machine['y'], machine['rotation']

            print(f"\n=== PIPE-TO-GROUND at x: {x}, y: {y}, rotation: {rotation} ===")

            # Calculate opposite rotation
            opposite_rotation = (rotation + 8) % 16

            # Search in the OPPOSITE direction (where the pipe opening is)
            search_rotation = opposite_rotation

            # Search multiple distances ahead to find matching pipe-to-ground
            for distance in range(1, max_distance + 1):
                searchx, searchy = get_search_coords(x, y, search_rotation, distance)
                print(f"  Searching at distance {distance}: x: {searchx}, y: {searchy}")

                other = coord_lookup.get((searchx, searchy))

                if other and other['machine_name'] in check_to:
                    # If we find a pipe-to-ground with the SAME rotation, stop searching (blocked)
                    if other['rotation'] == rotation:
                        print(f"    ✗ Found pipe-to-ground with SAME rotation {rotation} - blocking, stop searching")
                        break

                    # Pipe-to-ground must have opposite rotation to connect
                    if other['rotation'] == opposite_rotation:
                        edges.append({
                            "from_name": machine['machine_name'],
                            "from_x": x,
                            "from_y": y,
                            "to_name": other['machine_name'],
                            "to_x": searchx,
                            "to_y": searchy
                        })
                        print(
                            f"    ✓ Found matching pipe-to-ground: {machine['machine_name']}({x},{y}) rotation {rotation} -> {other['machine_name']}({searchx},{searchy}) rotation {other['rotation']}")
                        break  # Found the pair, stop searching
                    else:
                        print(
                            f"    ✗ Found pipe-to-ground but rotation doesn't match (expected {opposite_rotation}, got {other['rotation']})")

        return edges

    # Handle underground belt pairing logic (same rotations)
    if is_underground_belt:
        coord_lookup = {}
        for m in machine_list:
            coord_lookup[(m['x'], m['y'])] = m

        for machine in machine_list:
            if machine['machine_name'] not in check_from:
                continue

            x, y, rotation = machine['x'], machine['y'], machine['rotation']

            print(f"\n=== UNDERGROUND BELT at x: {x}, y: {y}, rotation: {rotation} ===")

            # Search multiple distances ahead to find matching underground belt
            for distance in range(1, max_distance + 1):
                searchx, searchy = get_search_coords(x, y, rotation, distance)
                print(f"  Searching at distance {distance}: x: {searchx}, y: {searchy}")

                other = coord_lookup.get((searchx, searchy))

                if other and other['machine_name'] in check_to:
                    # Both underground belts must have the same rotation
                    if other['rotation'] == rotation:
                        edges.append({
                            "from_name": machine['machine_name'],
                            "from_x": x,
                            "from_y": y,
                            "to_name": other['machine_name'],
                            "to_x": searchx,
                            "to_y": searchy
                        })
                        print(
                            f"    ✓ Found matching underground belt: {machine['machine_name']}({x},{y}) -> {other['machine_name']}({searchx},{searchy})")
                        break  # Found the pair, stop searching
                    else:
                        print(
                            f"    ✗ Found underground belt but rotation doesn't match: {other['rotation']} != {rotation}")

        return edges

    # Standard edge detection logic
    coord_lookup = {}
    for m in machine_list:
        coord_lookup[(m['x'], m['y'])] = m

    for machine in machine_list:
        if machine['machine_name'] not in check_from:
            continue

        x, y, rotation = machine['x'], machine['y'], machine['rotation']
        base = rotation
        rot_plus = (rotation + 4) % 16
        rot_minus = (rotation - 4) % 16

        print(f"Original Position\t x: {x}, y: {y}, rotation: {rotation}")

        for distance in range(1, max_distance + 1):
            searchx, searchy = get_search_coords(x, y, rotation, distance)
            print(f"EDGE SEARCH POSITION\t x: {searchx}, y: {searchy}, rotation: {rotation}")
            other = coord_lookup.get((searchx, searchy))

            if other and other['machine_name'] in check_to:
                # For strict rotation, require exact rotation match
                if strict_rotation:
                    rotation_match = (other['rotation'] == base)
                else:
                    rotation_match = (other['rotation'] in [base, rot_plus, rot_minus])

                # Check if search coordinates are within the target's selection box
                if check_selection_box:
                    if not is_point_in_selection_box(searchx, searchy, other['selection_box']):
                        print(
                            f"  ❌ Search coords ({searchx}, {searchy}) NOT in selection box of {other['machine_name']}")
                        continue
                    else:
                        print(f"  ✓ Search coords ({searchx}, {searchy}) IN selection box of {other['machine_name']}")

                if rotation_match:
                    edges.append({
                        "from_name": machine['machine_name'],
                        "from_x": x,
                        "from_y": y,
                        "to_name": other['machine_name'],
                        "to_x": searchx,
                        "to_y": searchy
                    })
                    print(f"{machine['machine_name']},{x},{y} -> {other['machine_name']},{searchx},{searchy}")

    return edges


def find_pipe_edges(machine_list):
    """Find pipe-to-pipe connections in a + shape, removing duplicates."""
    edges = []
    coord_lookup = {}

    # Build coordinate lookup for pipes
    for m in machine_list:
        if m['machine_name'] == 'pipe':
            coord_lookup[(m['x'], m['y'])] = m

    # For each pipe, check all 4 directions
    for machine in machine_list:
        if machine['machine_name'] != 'pipe':
            continue

        x, y = machine['x'], machine['y']
        print(f"\n=== PIPE at x: {x}, y: {y} ===")

        # Check all 4 directions (+ shape)
        directions = [
            (x, y - 1),  # North
            (x + 1, y),  # East
            (x, y + 1),  # South
            (x - 1, y)  # West
        ]

        for check_x, check_y in directions:
            print(f"  Checking direction: x: {check_x}, y: {check_y}")
            other = coord_lookup.get((check_x, check_y))

            if other:
                edges.append({
                    "from_name": machine['machine_name'],
                    "from_x": x,
                    "from_y": y,
                    "to_name": other['machine_name'],
                    "to_x": check_x,
                    "to_y": check_y
                })
                print(f"    ✓ Found pipe connection: ({x},{y}) -> ({check_x},{check_y})")

    # Remove duplicate edges (keep only one direction per connection)
    seen = set()
    deduplicated_edges = []

    for edge in edges:
        # Create a normalized key (smaller coords first)
        coord1 = (edge['from_x'], edge['from_y'])
        coord2 = (edge['to_x'], edge['to_y'])
        edge_key = tuple(sorted([coord1, coord2]))

        if edge_key not in seen:
            seen.add(edge_key)
            deduplicated_edges.append(edge)

    print(f"\n=== PIPE DEDUPLICATION ===")
    print(f"Original pipe edges: {len(edges)}")
    print(f"After deduplication: {len(deduplicated_edges)}")

    return deduplicated_edges


def find_chemical_plant_pipe_edges(machine_list):
    """Find pipe connections to chemical plants based on rotation."""
    edges = []
    coord_lookup = {}

    # Build coordinate lookup for pipes and pipe-to-ground
    for m in machine_list:
        if m['machine_name'] in ('pipe', 'pipe-to-ground'):
            coord_lookup[(m['x'], m['y'])] = m

    # For each chemical plant, check pipe connection points based on rotation
    for machine in machine_list:
        if machine['machine_name'] != 'chemical-plant':
            continue

        x, y, rotation = machine['x'], machine['y'], machine['rotation']
        print(f"\n=== CHEMICAL PLANT at x: {x}, y: {y}, rotation: {rotation} ===")

        # Define pipe connection offsets and required rotations for each chemical plant rotation
        # For pipe-to-ground: "in" side (same rotation) vs "out" side (opposite rotation)

        pipe_connections = []

        if rotation == 0:  # North (arrow pointing up)
            pipe_connections = [
                {'offset': (-1, -2), 'required_rotation': 8, 'side': 'top-left'},
                # Top pipes need opposite rotation (pointing down towards plant)
                {'offset': (1, -2), 'required_rotation': 8, 'side': 'top-right'},
                {'offset': (-1, 2), 'required_rotation': 0, 'side': 'bottom-left'},
                # Bottom pipes need same rotation (pointing up towards plant)
                {'offset': (1, 2), 'required_rotation': 0, 'side': 'bottom-right'}
            ]
        elif rotation == 4:  # East (arrow pointing right)
            pipe_connections = [
                {'offset': (2, -1), 'required_rotation': 12, 'side': 'right-top'},
                # Right pipes need opposite rotation (pointing left towards plant)
                {'offset': (2, 1), 'required_rotation': 12, 'side': 'right-bottom'},
                {'offset': (-2, -1), 'required_rotation': 4, 'side': 'left-top'},
                # Left pipes need same rotation (pointing right towards plant)
                {'offset': (-2, 1), 'required_rotation': 4, 'side': 'left-bottom'}
            ]
        elif rotation == 8:  # South (arrow pointing down)
            pipe_connections = [
                {'offset': (1, 2), 'required_rotation': 0, 'side': 'bottom-right'},
                # Bottom pipes need opposite rotation (pointing up towards plant)
                {'offset': (-1, 2), 'required_rotation': 0, 'side': 'bottom-left'},
                {'offset': (1, -2), 'required_rotation': 8, 'side': 'top-right'},
                # Top pipes need same rotation (pointing down towards plant)
                {'offset': (-1, -2), 'required_rotation': 8, 'side': 'top-left'}
            ]
        elif rotation == 12:  # West (arrow pointing left)
            pipe_connections = [
                {'offset': (-2, 1), 'required_rotation': 4, 'side': 'left-bottom'},
                # Left pipes need opposite rotation (pointing right towards plant)
                {'offset': (-2, -1), 'required_rotation': 4, 'side': 'left-top'},
                {'offset': (2, 1), 'required_rotation': 12, 'side': 'right-bottom'},
                # Right pipes need same rotation (pointing left towards plant)
                {'offset': (2, -1), 'required_rotation': 12, 'side': 'right-top'}
            ]

        # Check each pipe connection point
        for connection in pipe_connections:
            offset_x, offset_y = connection['offset']
            required_rotation = connection['required_rotation']
            side = connection['side']

            check_x = x + offset_x
            check_y = y + offset_y
            print(f"  Checking {side} at: x: {check_x}, y: {check_y}")

            pipe = coord_lookup.get((check_x, check_y))

            if pipe:
                # If it's a regular pipe, always connect
                if pipe['machine_name'] == 'pipe':
                    edges.append({
                        "from_name": pipe['machine_name'],
                        "from_x": check_x,
                        "from_y": check_y,
                        "to_name": machine['machine_name'],
                        "to_x": x,
                        "to_y": y
                    })
                    print(
                        f"    ✓ Found pipe connection: {pipe['machine_name']}({check_x},{check_y}) -> chemical-plant({x},{y})")

                # If it's pipe-to-ground, check rotation
                elif pipe['machine_name'] == 'pipe-to-ground':
                    if pipe['rotation'] == required_rotation:
                        edges.append({
                            "from_name": pipe['machine_name'],
                            "from_x": check_x,
                            "from_y": check_y,
                            "to_name": machine['machine_name'],
                            "to_x": x,
                            "to_y": y
                        })
                        print(
                            f"    ✓ Found pipe-to-ground connection: {pipe['machine_name']}({check_x},{check_y}) rotation {pipe['rotation']} -> chemical-plant({x},{y})")
                    else:
                        print(
                            f"    ✗ pipe-to-ground rotation mismatch: expected {required_rotation}, got {pipe['rotation']}")

    return edges


def find_oil_ref_pipe_edges(machine_list):
    edges = []
    coord_lookup = {}
    for m in machine_list:
        if m['machine_name'] in ('pipe', 'pipe-to-ground'):
            coord_lookup[(m['x'], m['y'])] = m
    for machine in machine_list:
        if machine['machine_name'] != 'oil-refinery':
            continue

        x, y, rotation = machine['x'], machine['y'], machine['rotation']
        print(f"\n=== oil-refinery at x: {x}, y: {y}, rotation: {rotation} ===")

        pipe_connections = []

        if rotation == 0:  # North (arrow pointing up)
            pipe_connections = [
                # {'offset': (-2, -3), 'required_rotation': 8, 'side': 'top-left'},      # Top pipes need opposite rotation (pointing down towards plant)
                {'offset': (2, -3), 'required_rotation': 8, 'side': 'top-right'},
                # {'offset': (-1, 3), 'required_rotation': 0, 'side': 'bottom-left'},    # Bottom pipes need same rotation (pointing up towards plant)
                {'offset': (1, 3), 'required_rotation': 0, 'side': 'bottom-right'}
            ]
        elif rotation == 4:  # East (arrow pointing right)
            pipe_connections = [
                # {'offset': (3, -2), 'required_rotation': 12, 'side': 'right-top'},      # Right pipes need opposite rotation (pointing left towards plant)
                {'offset': (3, 2), 'required_rotation': 12, 'side': 'right-bottom'},
                # {'offset': (-3, -1), 'required_rotation': 4, 'side': 'left-top'},       # Left pipes need same rotation (pointing right towards plant)
                {'offset': (-3, 1), 'required_rotation': 4, 'side': 'left-bottom'}
            ]
        elif rotation == 8:  # South (arrow pointing down)
            pipe_connections = [
                # {'offset': (1, 3), 'required_rotation': 0, 'side': 'bottom-right'},     # Bottom pipes need opposite rotation (pointing up towards plant)
                {'offset': (-1, 3), 'required_rotation': 0, 'side': 'bottom-left'},
                # {'offset': (2, -3), 'required_rotation': 8, 'side': 'top-right'},       # Top pipes need same rotation (pointing down towards plant)
                {'offset': (-2, -3), 'required_rotation': 8, 'side': 'top-left'}
            ]
        elif rotation == 12:  # West (arrow pointing left)
            pipe_connections = [
                # {'offset': (-3, 1), 'required_rotation': 4, 'side': 'left-bottom'},     # Left pipes need opposite rotation (pointing right towards plant)
                {'offset': (-3, -1), 'required_rotation': 4, 'side': 'left-top'},
                # {'offset': (3, 2), 'required_rotation': 12, 'side': 'right-bottom'},    # Right pipes need same rotation (pointing left towards plant)
                {'offset': (3, -2), 'required_rotation': 12, 'side': 'right-top'}
            ]

        # Check each pipe connection point
        for connection in pipe_connections:
            offset_x, offset_y = connection['offset']
            required_rotation = connection['required_rotation']
            side = connection['side']

            check_x = x + offset_x
            check_y = y + offset_y
            print(f"  Checking {side} at: x: {check_x}, y: {check_y}")

            pipe = coord_lookup.get((check_x, check_y))

            if pipe:
                # If it's a regular pipe, always connect
                if pipe['machine_name'] == 'pipe':
                    edges.append({
                        "from_name": pipe['machine_name'],
                        "from_x": check_x,
                        "from_y": check_y,
                        "to_name": machine['machine_name'],
                        "to_x": x,
                        "to_y": y
                    })
                    print(
                        f"    ✓ Found pipe connection: {pipe['machine_name']}({check_x},{check_y}) -> oil-refinery({x},{y})")

                # If it's pipe-to-ground, check rotation
                elif pipe['machine_name'] == 'pipe-to-ground':
                    if pipe['rotation'] == required_rotation:
                        edges.append({
                            "from_name": pipe['machine_name'],
                            "from_x": check_x,
                            "from_y": check_y,
                            "to_name": machine['machine_name'],
                            "to_x": x,
                            "to_y": y
                        })
                        print(
                            f"    ✓ Found pipe-to-ground connection: {pipe['machine_name']}({check_x},{check_y}) rotation {pipe['rotation']} -> oil-refinery({x},{y})")
                    else:
                        print(
                            f"    ✗ pipe-to-ground rotation mismatch: expected {required_rotation}, got {pipe['rotation']}")

    return edges


def find_steam_engine_pipe_edges(machine_list):
    edges = []
    coord_lookup = {}
    for m in machine_list:
        if m['machine_name'] in ('pipe', 'pipe-to-ground'):
            coord_lookup[(m['x'], m['y'])] = m
    for machine in machine_list:
        if machine['machine_name'] != 'steam-engine':
            continue

        x, y, rotation = machine['x'], machine['y'], machine['rotation']
        print(f"\n=== oil-refinery at x: {x}, y: {y}, rotation: {rotation} ===")

        pipe_connections = []

        if rotation == 0:  # North (arrow pointing up)
            pipe_connections = [
                # {'offset': (-2, -3), 'required_rotation': 8, 'side': 'top-left'},      # Top pipes need opposite rotation (pointing down towards plant)
                {'offset': (0, -3), 'required_rotation': 8, 'side': 'top-right'},
                # {'offset': (-1, 3), 'required_rotation': 0, 'side': 'bottom-left'},    # Bottom pipes need same rotation (pointing up towards plant)
                {'offset': (0, 3), 'required_rotation': 0, 'side': 'bottom-right'}
            ]
        elif rotation == 4:  # East (arrow pointing right)
            pipe_connections = [
                # {'offset': (3, -2), 'required_rotation': 12, 'side': 'right-top'},      # Right pipes need opposite rotation (pointing left towards plant)
                {'offset': (3, 0), 'required_rotation': 12, 'side': 'right-bottom'},
                # {'offset': (-3, -1), 'required_rotation': 4, 'side': 'left-top'},       # Left pipes need same rotation (pointing right towards plant)
                {'offset': (-3, 0), 'required_rotation': 4, 'side': 'left-bottom'}
            ]
        elif rotation == 8:  # South (arrow pointing down)
            pipe_connections = [
                # {'offset': (1, 3), 'required_rotation': 0, 'side': 'bottom-right'},     # Bottom pipes need opposite rotation (pointing up towards plant)
                # {'offset': (-1, 3), 'required_rotation': 0, 'side': 'bottom-left'},
                # {'offset': (2, -3), 'required_rotation': 8, 'side': 'top-right'},       # Top pipes need same rotation (pointing down towards plant)
                # {'offset': (-2, -3), 'required_rotation': 8, 'side': 'top-left'}
            ]
        elif rotation == 12:  # West (arrow pointing left)
            pipe_connections = [
                # {'offset': (-3, 1), 'required_rotation': 4, 'side': 'left-bottom'},     # Left pipes need opposite rotation (pointing right towards plant)
                # {'offset': (-3, -1), 'required_rotation': 4, 'side': 'left-top'},
                # {'offset': (3, 2), 'required_rotation': 12, 'side': 'right-bottom'},    # Right pipes need same rotation (pointing left towards plant)
                # {'offset': (3, -2), 'required_rotation': 12, 'side': 'right-top'}
            ]

        # Check each pipe connection point
        for connection in pipe_connections:
            offset_x, offset_y = connection['offset']
            required_rotation = connection['required_rotation']
            side = connection['side']

            check_x = x + offset_x
            check_y = y + offset_y
            print(f"  Checking {side} at: x: {check_x}, y: {check_y}")

            pipe = coord_lookup.get((check_x, check_y))

            if pipe:
                # If it's a regular pipe, always connect
                if pipe['machine_name'] == 'pipe':
                    edges.append({
                        "from_name": pipe['machine_name'],
                        "from_x": check_x,
                        "from_y": check_y,
                        "to_name": machine['machine_name'],
                        "to_x": x,
                        "to_y": y
                    })
                    print(
                        f"    ✓ Found pipe connection: {pipe['machine_name']}({check_x},{check_y}) -> oil-refinery({x},{y})")

                # If it's pipe-to-ground, check rotation
                elif pipe['machine_name'] == 'pipe-to-ground':
                    if pipe['rotation'] == required_rotation:
                        edges.append({
                            "from_name": pipe['machine_name'],
                            "from_x": check_x,
                            "from_y": check_y,
                            "to_name": machine['machine_name'],
                            "to_x": x,
                            "to_y": y
                        })
                        print(
                            f"    ✓ Found pipe-to-ground connection: {pipe['machine_name']}({check_x},{check_y}) rotation {pipe['rotation']} -> oil-refinery({x},{y})")
                    else:
                        print(
                            f"    ✗ pipe-to-ground rotation mismatch: expected {required_rotation}, got {pipe['rotation']}")

    return edges


def find_boiler_pipe_edges(machine_list):
    edges = []
    coord_lookup = {}
    for m in machine_list:
        if m['machine_name'] in ('pipe', 'pipe-to-ground'):
            coord_lookup[(m['x'], m['y'])] = m
    for machine in machine_list:
        if machine['machine_name'] != 'boiler':
            continue

        x, y, rotation = machine['x'], machine['y'], machine['rotation']
        print(f"\n=== oil-refinery at x: {x}, y: {y}, rotation: {rotation} ===")

        pipe_connections = []

        if rotation == 0:  # North (arrow pointing up)
            pipe_connections = [
                {'offset': (0, -1.5), 'required_rotation': 8, 'side': 'top'},
                # Top pipe needs opposite rotation (pointing down towards plant)
                {'offset': (2, 0), 'required_rotation': 12, 'side': 'right'},
                # Right pipe needs rotation 12 (pointing left)
                {'offset': (-2, 0), 'required_rotation': 4, 'side': 'left'},
                # Left pipe needs rotation 4 (pointing right)
            ]
        elif rotation == 4:  # East (arrow pointing right)
            pipe_connections = [
                {'offset': (2, 0), 'required_rotation': 12, 'side': 'right'},
                # Right pipe needs opposite rotation (pointing left towards plant)
                {'offset': (0, 2), 'required_rotation': 0, 'side': 'bottom'},
                # Bottom pipe needs rotation 0 (pointing up)
                {'offset': (0, -2), 'required_rotation': 8, 'side': 'top'},  # Top pipe needs rotation 8 (pointing down)
            ]
        elif rotation == 8:  # South (arrow pointing down)
            pipe_connections = [
                {'offset': (0, 2), 'required_rotation': 0, 'side': 'bottom'},
                # Bottom pipe needs opposite rotation (pointing up towards plant)
                {'offset': (-2, 0), 'required_rotation': 4, 'side': 'left'},
                # Left pipe needs rotation 4 (pointing right)
                {'offset': (2, 0), 'required_rotation': 12, 'side': 'right'},
                # Right pipe needs rotation 12 (pointing left)
            ]
        elif rotation == 12:  # West (arrow pointing left)
            pipe_connections = [
                {'offset': (-2, 0), 'required_rotation': 4, 'side': 'left'},
                # Left pipe needs opposite rotation (pointing right towards plant)
                {'offset': (0, -2), 'required_rotation': 8, 'side': 'top'},  # Top pipe needs rotation 8 (pointing down)
                {'offset': (0, 2), 'required_rotation': 0, 'side': 'bottom'},
                # Bottom pipe needs rotation 0 (pointing up)
            ]

        # Check each pipe connection point
        for connection in pipe_connections:
            offset_x, offset_y = connection['offset']
            required_rotation = connection['required_rotation']
            side = connection['side']

            check_x = x + offset_x
            check_y = y + offset_y
            print(f"  Checking {side} at: x: {check_x}, y: {check_y}")

            pipe = coord_lookup.get((check_x, check_y))

            if pipe:
                # If it's a regular pipe, always connect
                if pipe['machine_name'] == 'pipe':
                    edges.append({
                        "from_name": pipe['machine_name'],
                        "from_x": check_x,
                        "from_y": check_y,
                        "to_name": machine['machine_name'],
                        "to_x": x,
                        "to_y": y
                    })
                    print(
                        f"    ✓ Found pipe connection: {pipe['machine_name']}({check_x},{check_y}) -> boiler({x},{y})")

                # If it's pipe-to-ground, check rotation
                elif pipe['machine_name'] == 'pipe-to-ground':
                    if pipe['rotation'] == required_rotation:
                        edges.append({
                            "from_name": pipe['machine_name'],
                            "from_x": check_x,
                            "from_y": check_y,
                            "to_name": machine['machine_name'],
                            "to_x": x,
                            "to_y": y
                        })
                        print(
                            f"    ✓ Found pipe-to-ground connection: {pipe['machine_name']}({check_x},{check_y}) rotation {pipe['rotation']} -> boiler({x},{y})")
                    else:
                        print(
                            f"    ✗ pipe-to-ground rotation mismatch: expected {required_rotation}, got {pipe['rotation']}")

    return edges


# --- Find edges ---
# 1️⃣ Transport belts (including fast belts)
edges1 = find_edges(
    machines,
    check_from=('transport-belt', 'fast-transport-belt'),
    check_to=('transport-belt', 'fast-transport-belt'),
    max_distance=1
)

# 2️⃣ Electric mining drills → transport belts (check selection box)
edges2 = find_edges(
    machines,
    check_from=('electric-mining-drill',),
    check_to=('transport-belt',),
    max_distance=2,
    check_selection_box=True
)

# 3️⃣ Transport → underground belts (strict rotation required)
edges3 = find_edges(
    machines,
    check_from=('transport-belt',),
    check_to=('underground-belt',),
    max_distance=1,
    strict_rotation=True
)

# 4️⃣ Underground belt pairs (special handling)
edges4 = find_edges(
    machines,
    check_from=('underground-belt',),
    check_to=('underground-belt',),
    max_distance=4,
    is_underground_belt=True
)

# 5️⃣ Inserter connections (special handling - includes long-handed)
edges5 = find_edges(
    machines,
    check_from=('inserter', 'fast-inserter', 'long-handed-inserter', 'stack-inserter'),
    check_to=('assembling-machine', 'transport-belt', 'chemical-plant', 'oil-refinery', 'lab'),
    is_inserter=True
)

# 6️⃣ Pipe-to-ground pairs (opposite rotations)
edges6 = find_edges(
    machines,
    check_from=('pipe-to-ground',),
    check_to=('pipe-to-ground',),
    max_distance=9,
    is_pipe_to_ground=True
)

# 7️⃣ Pipe-to-pipe connections (+ shape, deduplicated)
edges7 = find_pipe_edges(machines)

# 8️⃣ Chemical plant to pipe connections
edges8 = find_chemical_plant_pipe_edges(machines)

edges9 = find_oil_ref_pipe_edges(machines)

edges10 = find_steam_engine_pipe_edges(machines)

edges11 = find_boiler_pipe_edges(machines)

# Combine all edges
all_edges = edges1 + edges2 + edges3 + edges4 + edges5 + edges6 + edges7 + edges8 + edges9 + edges10 + edges11

# --- Output edges ---
print("\n=== ALL EDGES ===")
for e in all_edges:
    print(e)
print(f"Total edges: {len(all_edges)}")