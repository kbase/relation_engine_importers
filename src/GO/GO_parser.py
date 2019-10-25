import obo_parser
import json

url = 'http://purl.obolibrary.org/obo/go.obo'
graph = obo_parser.read_obo(url)

list_of_edges = list(graph.edges)
list_of_nodes = list(graph.node)


def write_relationship_edges(relationship_edges):
    for edge in list_of_edges:
        if edge[2] != 'is_a':
            edge_dict = {}
            edge_dict['_key'] = str(edge[0] + "__" + edge[1] + "__" + edge[2])
            edge_dict['_from'] = "GO_term/" + edge[0]
            edge_dict['_to'] = "GO_term/" + edge[1]
            edge_dict['relationship_type'] = edge[2]
            relationship_edges.write(json.dumps(edge_dict) + "\n")


def write_isa_edges(isa_edges):
    for edge in list_of_edges:
        if edge[2] == 'is_a':
            edge_dict = {}
            edge_dict['_key'] = str(edge[0] + "__" + edge[1] + "__is_a")
            edge_dict['_from'] = "GO_term/" + edge[0]
            edge_dict['_to'] = "GO_term/" + edge[1]
            isa_edges.write(json.dumps(edge_dict) + "\n")


def write_intersection_edges(intersection_edges):
    for i in range(len(graph.node)):
        curr_node = list_of_nodes[i]
        if 'intersection_of' in graph.node[curr_node]:
            for val in graph.node[curr_node]['intersection_of']:
                edge_dict = {}
                intersection_term = val.split(" ")
                if len(intersection_term) == 1:
                    edge_dict['_key'] = str(curr_node + "__" + intersection_term[0] + "__")
                    edge_dict["_from"] = "GO_term/" + curr_node
                    edge_dict["_to"] = "GO_term/" + intersection_term[0]
                    edge_dict["intersection_type"] = ""
                else:
                    edge_dict['_key'] = str(curr_node + "__" + intersection_term[1] + "__" + intersection_term[0])
                    edge_dict["_from"] = "GO_term/" + curr_node
                    edge_dict["_to"] = "GO_term/" + intersection_term[1]
                    edge_dict["intersection_type"] = intersection_term[0]
                intersection_edges.write(json.dumps(edge_dict) + "\n")


def write_disjoint_edges(disjoint_edges):
    for i in range(len(graph.node)):
        curr_node = list_of_nodes[i]
        if 'disjoint_from' in graph.node[curr_node]:
            edge_dict = {}
            for val in graph.node[curr_node]['disjoint_from']:
                edge_dict['_key'] = str(curr_node + "__" + val + "__disjoint_from")
                edge_dict["_from"] = "GO_term/" + curr_node
                edge_dict["_to"] = "GO_term/" + val
                disjoint_edges.write(json.dumps(edge_dict) + "\n")


def write_consider_edges(consider_edges):
    for i in range(len(graph.node)):
        curr_node = list_of_nodes[i]
        if 'consider' in graph.node[curr_node]:
            edge_dict = {}
            for val in graph.node[curr_node]['consider']:
                edge_dict['_key'] = str(curr_node + "__" + val + "__consider")
                edge_dict["_from"] = "GO_term/" + curr_node
                edge_dict["_to"] = "GO_term/" + val
                consider_edges.write(json.dumps(edge_dict) + "\n")


def write_replaced_edges(replaced_edges):
    for i in range(len(graph.node)):
        curr_node = list_of_nodes[i]
        if 'replaced_by' in graph.node[curr_node]:
            edge_dict = {}
            for val in graph.node[curr_node]['replaced_by']:
                edge_dict['_key'] = str(curr_node + "__" + val + "__replaced_by")
                edge_dict["_from"] = "GO_term/" + curr_node
                edge_dict["_to"] = "GO_term/" + val
                replaced_edges.write(json.dumps(edge_dict) + "\n")


def write_terms(nodes_output):
    for i in range(len(list_of_nodes)):
        node_dict = {}
        node_dict['_key'] = list_of_nodes[i]
        node_dict['name'] = graph.node[list_of_nodes[i]]['name']
        node_dict['namespace'] = graph.node[list_of_nodes[i]]['namespace']
        if 'alt_id' in graph.node[list_of_nodes[i]]:
            node_dict['alt_id'] = graph.node[list_of_nodes[i]]['alt_id']
        if 'def' in graph.node[list_of_nodes[i]]:
            node_dict['def'] = graph.node[list_of_nodes[i]]['def']
        if 'comment' in graph.node[list_of_nodes[i]]:
            node_dict['comment'] = graph.node[list_of_nodes[i]]['comment']
        if 'synonym' in graph.node[list_of_nodes[i]]:
            node_dict['synonym'] = graph.node[list_of_nodes[i]]['synonym']
        if 'xref' in graph.node[list_of_nodes[i]]:
            node_dict['xref'] = graph.node[list_of_nodes[i]]['xref']
        if 'is_obsolete' in graph.node[list_of_nodes[i]]:
            node_dict['is_obsolete'] = graph.node[list_of_nodes[i]]['is_obsolete']
        if 'replaced_by' in graph.node[list_of_nodes[i]]:
            node_dict['replaced_by'] = graph.node[list_of_nodes[i]]['replaced_by']
        if 'consider' in graph.node[list_of_nodes[i]]:
            node_dict['consider'] = graph.node[list_of_nodes[i]]['consider']
        if 'created_by' in graph.node[list_of_nodes[i]]:
            node_dict['created_by'] = graph.node[list_of_nodes[i]]['created_by']
        if 'creation_date' in graph.node[list_of_nodes[i]]:
            node_dict['creation_date'] = graph.node[list_of_nodes[i]]['creation_date']
        nodes_output.write(json.dumps(node_dict) + "\n")


relationship_edges_path = 'GO_edges_relationship.json'
isa_edges_path = 'GO_edges_isa.json'
intersection_edges_path = 'GO_edges_intersection_of.json'
disjoint_edges_path = 'GO_edges_disjoint_from.json'
consider_edges_path = 'GO_edges_consider.json'
replaced_edges_path = 'GO_edges_replaced_by.json'
nodes_path = "GO_term.json"

relationship_edges = open(relationship_edges_path, 'w')
isa_edges = open(isa_edges_path, 'w')
intersection_edges = open(intersection_edges_path, 'w')
disjoint_edges = open(disjoint_edges_path, 'w')
consider_edges = open(consider_edges_path, 'w')
replaced_edges = open(replaced_edges_path, 'w')
nodes_output = open(nodes_path, "w")

to_close = [relationship_edges, isa_edges, intersection_edges,
            disjoint_edges, consider_edges, replaced_edges, nodes_output]

write_relationship_edges(relationship_edges)
write_isa_edges(isa_edges)
write_intersection_edges(intersection_edges)
write_disjoint_edges(disjoint_edges)
write_consider_edges(consider_edges)
write_replaced_edges(replaced_edges)
write_terms(nodes_output)

for file in to_close:
    file.close()
