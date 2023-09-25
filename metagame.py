"""
Created on Mon Sep 12 15:05:44 2022

@author: ToupinC
"""

from graph import Card, Edge, Path
from visual_styles import DEFAULT_COLOR, DEFAULT_NODE_SIZE, DEFAULT_EDGE_WIDTH
       
class Format:
    '''A format in a metagame contains a set of edges between cards in the game. It is similar to a graph 
    except that the card objects belong to the parent metagame rather than the format itself.'''
    def __init__(self, metagame, format_name, *edges):
        if not all([isinstance(edge, Edge) for edge in edges]):
            raise TypeError("All edges must be valid Edge objects.")
        if not all([(edge.source  in metagame.cards.values()) and (edge.target in metagame.cards.values()) for edge in edges]):
            raise ValueError("All edges must be between nodes in the market.")
        # Ensure there are no duplicate edges within a sector. 
        #Duplicate edges being passed to the app layer prevents anything from displaying.
        edges = sorted(list(edges), key = lambda x: str(x))
        for i in reversed(range(len(edges)-1)):
            if str(edges[i]) == str(edges[i+1]):
                del edges[i]
       
        
        self.metagame = metagame
        self.name = format_name
        # Hash edges so they can be quickly retrieved by their IDs, their source node IDs, or their target node IDs.
        self.edges = {edge.id: edge for edge in edges}
        self.edges_at_card = {card.id: [edge for edge in edges if edge.source.id == card.id or edge.target.id == card.id] 
                              for card in metagame.cards.values()}
        return
    
    # Handles the minutia of adding a new edge to a sector
    def add(self, new_edge):
        if not isinstance(new_edge, Edge):
            raise TypeError("Can only add valid edge objects to a format.")
        if new_edge.source.id not in self.market.node_table or new_edge.target.id not in self.market.nodes:
            raise ValueError("Edges must be between existing cards.")
        # Ensure edge is not a duplicate. Duplicate edges cause errors in the app layer
        if new_edge.id not in self.edges and str(new_edge) not in [str(edge) for edge in self.edges.values()]:
            self.edges[new_edge.id] = new_edge
        return
    
    # Retrieve edges by its ID
    def edge_by_id(self, edge_id):
        return self.edges.get(edge_id, None)
    # Retrieve edges by their source or target card ID
    def edges_at(self, card_id):
        return self.edges_at_card.get(card_id, None)
    
    # Given a particular card, returns the cards that are one edge away in any direction and the edges that connect them.
    def direct_neighbours(self, src_card):
        if not isinstance(src_card, Card):
            raise TypeError("Can only find the neighbourhood of a card.")
        edges = self.edges_at(src_card.id)
        cards = [src_card] + [edge.target for edge in edges] + [edge.source for edge in edges]
        
        return list(set(cards)), list(set(edges))
    
    # Given a particular card, returns the cards that are at most n edges away in any direction and the edges that connect them.
    def n_neighbours(self, src_card, n):
        if not isinstance(src_card, Card):
            raise TypeError("Can only find the neighbourhood of a card.")
        cards = [src_card]
        edges = []
        for i in range(n):
            for card in cards.copy():
                new_cards, new_edges = self.direct_neighbours(src_card)
                cards += new_cards
                edges += new_edges
        return list(set(cards)), list(set(edges))
    
    # Returns a dict with nodes and edges data formatted for the app layer to interpret it.
    def to_visdcc(self):
        visdcc_nodes = [{
            'id': card.id, 
            'label': card.name, 
            'Card Type': card.type, 
            'shape': 'dot',
            'size': DEFAULT_NODE_SIZE,
            'hidden': len(self.edges_at(card.id))==0,
            'color': DEFAULT_COLOR,
            'true_color': DEFAULT_COLOR,
            'deck_count': card.count,
            'Number of Decks': card.count[self.name],
            'total_copies': card.total,
            'Number of Copies': card.total[self.name],
            'Number of Neighbours': 1+len(self.edges_at(card.id)),
            'Number of 2-Neighbours': 1+len(self.n_neighbours(card, 2)[1]),
            'visibility': {'default': len(self.edges_at(card.id))>0},
            'lighten': {'default': False}
            } for card in self.metagame.cards.values() if len(self.edges_at(card.id))>0]
        visdcc_edges = [{
            'id': edge.id,
            'name': edge.id,
            'from': edge.source.id,
            'to': edge.target.id,
            'count': edge.count,
            'total': edge.total,
            'hidden': False,
            'color': {'color': DEFAULT_COLOR},
            'true_color': DEFAULT_COLOR,
            'formats': [],
            'width': DEFAULT_EDGE_WIDTH,
            'visibility': {'default': True},
            'lighten': {'default': False}
            } for edge in self.edges.values()]
        return {'nodes': visdcc_nodes, 'edges': visdcc_edges}
                
class Metagame():
    '''A metagame contains a set of cards and a set of formats within that metagame.'''
    def __init__(self, *cards):
        if any([not isinstance(card, Card) for card in cards]):
            raise TypeError("Can only import card objects into a metagame.")
        self.cards = {card.id: card for card in cards}
        self.formats = {}
        
    #Takes in list of cards and adds cards that are not pre-existing (based on id) to market
    def add_cards(self, *cards):
        if any([not isinstance(card, Card) for card in cards]):
            raise TypeError("Can only import card objects into a metagame.")
        for card in cards:
            if card.id not in self.cards:
                self.cards[card.id] = card
    #Takes in a string and a list of edges to create a new format object, and add it to the metagame's formats dict    
    def new_format(self, name, *edges):
        self.formats[name] = Format(self, name, *edges)
    #Takes in a list of ID values and returns all matching cards in the metagame    
    def cards_by_id(self, *card_ids):
        return [self.cards[card_id] for card_id in card_ids if card_id in self.cards]
    #Takes in a list of names and returns all cards with those names in the metagame
    def cards_by_name(self, *card_names):
        return [card for card in self.cards.values() if any([card_name in card.name for card_name in card_names])]
    #Takes in a format name and returns that format if it exists
    def get_format(self, format_name):
        return self.formats.get(format_name)
    def to_visdcc(self, default_format = 'All'):                
        visdcc = self.formats.get(default_format, self.formats['All']).to_visdcc()
        edge_dict = {edge['name']: edge for edge in visdcc['edges']}
        for format_key in self.formats:
            meta_format = self.formats[format_key]
            for edge in meta_format.edges.values():
                edge_dict[edge.source.id + '__' + edge.target.id]['formats'].append(format_key)
        visdcc['edges'] = list(edge_dict.values())
        return visdcc
    
    def __getitem__(self, key):
        return self.formats.get(key, self.formats['All'])
        