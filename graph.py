# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 01:06:59 2021

@author: ToupinC
"""
import uuid

class Card:
    '''A card is a Magic: the Gathering game object represented by a node in a graph.'''
    def __init__(self, card_name, card_type, count, total, node_id = None):
        if node_id is None:
            node_id = uuid.uuid4()
        self.name = card_name
        # The type of a card determines the role it plays in the game, e.g. Land, Creature, Artifact, etc.
        self.type = card_type
        # The count represents the number of decks this card has appeared in, broken down by format.
        self.count = count
        # The total represents the total number of copies of this card were played in the metagame, broken down by format.
        self.total = total
        self.id = str(node_id)
        return
    
    def __str__(self):
        return(self.name)
    
    def __repr__(self):
        return(self.name)
    
    # Subtracting cards C2-C1 creates an edge from C1 to C2
    def __sub__(self, other):
        if not isinstance(other, Card):
            raise TypeError('Can only create an Edge from another Card object.')
        return(Edge(other, self, 1, 1))
    
class Edge:
    '''An edge is an object that describes a relationship between two cards. In a MtG format, a 
    relationship between C1 and C2 denotes that these two cards appear in a metagame deck together.'''
    def __init__(self, source, target, count, total, edge_id = None):
        if edge_id is None:
            edge_id = source.id + '__' + target.id
        # Source denotes the start of an edge. This is arbitrary for a MtG format as the relationships are not directional.
        self.source = source
        # Target denotes the end of an edge. This is arbitrary for a MtG format as the relationships are not directional.
        self.target = target
        # The count represents the number of decks this relationship has appeared in within the observed metagame.
        self.count = count
        # The total represents the number of times this relationship has appeared in the metagame, accounting for multiple copies of cards within decks.
        self.total = total
        self.id = str(edge_id)
        return
    
    # Returns True if edge is a loop (starts and ends at same node)
    def is_loop(self):
        return self.source.id == self.target.id
    
    # Returns a path if an edge or path is added or a line if a line is added.
    def __add__(self, other):
        if not isinstance(other, Edge) and not isinstance(other, Path):
            raise TypeError("Can only add an edge or path to an edge.")
        return Path(self, other)
    
    def __repr__(self):
        return('{} -- {}'.format(self.source.name, self.target.name))
    
        
class Path:
    '''A path is a sequence of connected edges which never loops back on itself.'''
    def __init__(self, *summands):
        # Check that all summands are either paths or edges
        if not all([isinstance(summand, Edge) or isinstance(summand, Path) for summand in summands]):
            raise ValueError("Only paths and edges can be combined to make a path.")
        # Check that each summand is connected to the next
        if not all([len(set([summands[i-1].source.id, 
                             summands[i-1].target.id, 
                             summands[i].source.id,
                             summands[i].target.id])) == 3 for i in range(1,len(summands))]):
            raise ValueError("Paths must consist of connected edges.")
        # Check that no nodes are visited more than once
        #TODO CT This could be optimized
        edges = [edge for summand in summands for edge in ([summand] if isinstance(summand, Edge) else summand.edges)]
        nodes_visited = set([edge.source.id for edge in edges] + [edge.target.id for edge in edges])
        if len(nodes_visited) != len(edges) + 1:
            raise ValueError("All cards visited on a path must be unique.")
        # Create list of edges from summands
        self.edges = edges
        self.nodes = [edge.source.id for edge in self.edges] + [self.edges[-1].target.id]
        self.source = summands[0].source if summands[0].target.id in [summands[1].source.id, summands[1].target.id] else summands[0].target
        self.target = summands[-1].source if summands[-1].target.id in [summands[-2].source.id, summands[-2].target.id] else summands[-1].target
        return

    # Length of a path is the number of edges
    def __len__(self):
        return len(self.edges)
    
    # Indexing a path returns a subpath
    def __getitem__(self, indices):
        new_edges = self.edges[indices]
        return  Path(new_edges)
    
    # Adding a path or edge to a path returns another path
    def __add__(self, other):
        return Path(self, other)