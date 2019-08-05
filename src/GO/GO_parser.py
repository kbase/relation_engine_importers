def write_relationship_edges(relationship_edges):
    for edge in list_of_edges:
        if edge[2] == 'is_a':
            edge_dict = {}
            edge_dict['from'] = edge[0]
            edge_dict['to'] = edge[1]
            relationship_edges.write(json.dumps(edge_dict) + "\n")
            
def write_isa_edges(isa_edges):
    for edge in list_of_edges:
        if edge[2] != 'is_a':
            edge_dict = {}
            edge_dict['from'] = edge[0]
            edge_dict['to'] = edge[1]
            isa_edges.write(json.dumps(edge_dict) + "\n")
    
def write_intersection_edges(intersection_edges):
    for i in range(len(graph.node)):
        curr_node = list_of_nodes[i]
        if 'intersection_of' in graph.node[curr_node]:
            for val in graph.node[curr_node]['intersection_of']:
                edge_dict = {}
                intersection_term = val.split(" ")
                edge_dict["from"] = curr_node
                if len(intersection_term) == 1:
                    edge_dict["to"] = intersection_term[0]
                    edge_dict["intersection_type"] = ""
                else:
                    edge_dict["to"] = intersection_term[1]
                    edge_dict["intersection_type"] = intersection_term[0]
                intersection_edges.write(json.dumps(edge_dict) + "\n")
                
def write_disjoint_edges(disjoint_edges):
    for i in range(len(graph.node)):
        curr_node = list_of_nodes[i]
        if 'disjoint_from' in graph.node[curr_node]:
            edge_dict = {}
            for val in graph.node[curr_node]['disjoint_from']: 
                edge_dict["from"] = curr_node
                edge_dict["to"] = val
                disjoint_edges.write(json.dumps(edge_dict) + "\n")

relationship_edges_path = 'GO_relationship_edges.txt'
isa_edges_path = 'GO_isa_edges.txt'
intersection_edges_path = 'GO_intersection_edges.txt'
disjoint_edges_path = 'GO_disjoint_edges.txt'

relationship_edges = open(relationship_edges_path, 'w')
isa_edges = open(isa_edges_path, 'w')
intersection_edges = open(intersection_edges_path, 'w')
disjoint_edges = open(disjoint_edges_path, 'w')
to_close = [relationship_edges, isa_edges, intersection_edges, disjoint_edges]


write_relationship_edges(relationship_edges)
write_isa_edges(isa_edges)
write_intersection_edges(intersection_edges)
write_disjoint_edges(disjoint_edges)

for file in to_close: 
    file.close() 