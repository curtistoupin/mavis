# -*- coding: utf-8 -*-
"""
Created on Fri Sep 15 21:09:36 2022

@author: ToupinC
"""
from graph import Card, Edge
from metagame import Metagame
from tqdm import tqdm
import json
import dash
import dash_bootstrap_components as dbc
from visual_styles import get_node_and_edge_scaling_vars, get_distinct_colors, get_app_layout, create_color_legend, DEFAULT_NODE_SIZE, DEFAULT_NODE_COLOR
from dash.dependencies import Input, Output, State

class Mavis:
    def __init__(self):
        self.metagame = self._import_from_json('data/cards.json', 'data/edges.json')
        self.format = 'All'
        self.data = self.metagame.to_visdcc(self.format)
        self.scaling_vars = get_node_and_edge_scaling_vars(self.data)
        self.node_value_color_mapping = {}
        self.edge_value_color_mapping = {}
        self.nbhd_type = 'None'
        self.search_text = ''
        self.node_color_option = 'None'
        self.size_nodes_option = 'None'
        self.selection = {'nodes': [], 'edges':[]}
        self.selected_nodes = None
        self.nbhd_names = {'neighbours': "Direct Neighbours",
                           '2-neighbours': '2-Neighbours'}
        self.app = self.create()
        self.app.title = 'MAVis'
    
    def _import_from_json(self, card_json_fp, edge_json_fp):
        with open(card_json_fp, 'r') as card_file:
            card_json = json.load(card_file)
        with open(edge_json_fp, 'r') as edge_file:
            edge_json = json.load(edge_file)
        
        metagame = Metagame(*[Card(card_name, **card_details) for card_name, card_details in card_json.items()])
        for format_name, format_edges in tqdm(edge_json.items()):
            edges = [Edge(metagame.cards_by_name(edge['key'][0])[0],
                          metagame.cards_by_name(edge['key'][1])[0],
                          **edge['value']) 
                     for edge in format_edges if edge['value']['count'] > 5]
            metagame.new_format(format_name, *edges)
        
        return metagame

    def _callback_format_select(self, graph_data, format_selection):
        self.format = format_selection
        meta_format = self.metagame[format_selection]
        for node in graph_data['nodes']:
            node['Number of Decks'] = node['deck_count'].get(format_selection, 0)
            node['Number of Copies'] = node['total_copies'].get(format_selection, 0)
            node['visibility']['format'] = len(meta_format.edges_at(node['id'])) > 0
            node['hidden'] = not all(node['visibility'].values())
        for edge in graph_data['edges']:
            edge['visibility']['format'] = meta_format.edge_by_id(edge['id']) is not None
            edge['hidden'] = not all(edge['visibility'].values())
        self.scaling_vars = get_node_and_edge_scaling_vars(graph_data)
        graph_data = self._callback_size_nodes(graph_data)
        graph_data = self._callback_show_nbhd(graph_data)
        return graph_data
    
    def _search_lighten_color(self, colstr, factor=0.9):
        col_r = int(colstr[1:3],16)
        col_r = int(255 - (1-factor)*(255-col_r))
        col_r = hex(col_r)[2:]
                
        col_g = int(colstr[3:5],16)
        col_g = int(255 - (1-factor)*(255-col_g))
        col_g = hex(col_g)[2:]
                
        col_b = int(colstr[5:7],16)
        col_b = int(255 - (1-factor)*(255-col_b))
        col_b = hex(col_b)[2:]
        
        newcolstr = ('#' + col_r + col_g + col_b).upper()
        return newcolstr
    
    def _callback_search_graph(self, graph_data, search_text):
        nodes = graph_data['nodes']
        edges = graph_data['edges']
        for node in nodes:
            if search_text.lower() not in node['label'].lower():
                node['lighten']['search'] = True
            else:
                node['lighten']['search'] = False
            node['color'] = node['true_color'] if not any(node['lighten'].values()) else self._search_lighten_color(node['true_color'])
        graph_data['nodes'] = nodes
        if search_text:
            for edge in edges:
                edge['lighten']['search'] = True
                edge['color']['color'] = self._search_lighten_color(edge['true_color'])
        else:
            for edge in edges:
                edge['lighten']['search'] = False
                edge['color']['color'] = edge['true_color'] if not any(edge['lighten'].values()) else self._search_lighten_color(edge['true_color'])
        return graph_data
    
    def _callback_color_nodes(self, graph_data, color_nodes_value):
        value_color_mapping = {}
        if color_nodes_value is None or color_nodes_value.lower() == 'none':
            for node in graph_data['nodes']:
                node['true_color'] = DEFAULT_NODE_COLOR
                node['color'] = node['true_color'] if not any(node['lighten'].values()) else self.search_lighten_color(node['true_color'])
        else:
            unique_values = list(set([node[color_nodes_value] for node in graph_data['nodes']]))
            colors = get_distinct_colors(len(unique_values))
            value_color_mapping = {x:y for x,y in zip(unique_values, colors)}
            for node in graph_data['nodes']:
                node['true_color'] = value_color_mapping[node[color_nodes_value]]
                node['color'] = node['true_color'] if not any(node['lighten'].values()) else self._search_lighten_color(node['true_color'])
        return graph_data, value_color_mapping
    
    def _callback_size_nodes(self, graph_data):
        for node in graph_data['nodes']:
            node['size'] = DEFAULT_NODE_SIZE
        if self.size_nodes_option != 'None':
            min_scale = self.scaling_vars['node'][self.size_nodes_option]['min']
            max_scale = self.scaling_vars['node'][self.size_nodes_option]['max']
            scale_val = lambda x: 20*(x-min_scale)/(max_scale - min_scale)
            for node in graph_data['nodes']:
                node['size'] = DEFAULT_NODE_SIZE + scale_val(node[self.size_nodes_option])
        return graph_data
    
    def _callback_show_nbhd(self, graph_data):
        self.selected_nodes = [node for node in graph_data['nodes'] if node['id'] in self.selection['nodes']]
        
        if self.selection['nodes']:
            node_ids = self.selection['nodes']
            nodes = []
            edges = []
            for node_id in node_ids:
                source_node = self.metagame.cards_by_id(node_id)[0]
                meta_format = self.metagame[self.format]
                if self.nbhd_type == 'neighbours':
                    new_nodes, new_edges = meta_format.direct_neighbours(source_node)
                elif self.nbhd_type == '2-neighbours':
                    new_nodes, new_edges = meta_format.n_neighbours(source_node, 2)
                else:
                    new_nodes = [node for node in self.metagame.cards.values()]
                    new_edges = [edge for edge in self.metagame['All'].edges.values()]
                nodes += new_nodes
                edges += new_edges
            nodes = list(set(nodes))
            edges = list(set(edges))
            nbhd_node_ids = [str(node.id) for node in nodes]
            nbhd_edge_ids = [str(edge.id) for edge in edges]
            for node in graph_data['nodes']:
                if str(node['id']) in nbhd_node_ids:
                    node['visibility']['nbhd'] = True
                else:
                    node['visibility']['nbhd'] = False
                node['hidden'] = not all(node['visibility'].values())
            for edge in graph_data['edges']:
                if str(edge['id']) in nbhd_edge_ids:
                    edge['visibility']['nbhd'] = True
                else:
                    edge['visibility']['nbhd'] = False
                edge['hidden'] = not all(edge['visibility'].values())
        else:
            for node in graph_data['nodes']:
                node['visibility']['nbhd'] = True
                node['hidden'] = not all(node['visibility'].values())
            for edge in graph_data['edges']:
                edge['visibility']['nbhd'] = True
                edge['hidden'] = not all(edge['visibility'].values())
        return graph_data
    
    def create(self, directed = False, vis_opts = None):
        app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
        app.layout = get_app_layout(self.data, 
                                    list(self.metagame.formats.keys()), 
                                    color_legends = self.get_color_popover_legend_children(),
                                    directed = directed,
                                    vis_opts = vis_opts)
        
        @app.callback(
            Output('color-legend-popup', 'is_open'),
            [Input('color-legend-toggle', 'n_clicks')],
            [State('color-legend-popup', 'is_open')]
        )
        def toggle_popover(n, is_open):
            if n:
                return not is_open
            return is_open
        
        @app.callback(
            Output('export-csv', 'data'),
            Input('export-csv-button', 'n_clicks'),
            State('graph', 'data'),
            prevent_initial_call=True
        )
        def export_nbhd(n, graph_data):
            if self.selected_nodes and self.nbhd_type in self.nbhd_names.keys():
                name_str = ', '.join([node['label'] for node in self.selected_nodes]) + ' - ' + self.nbhd_names[self.nbhd_type] + '.csv'
            else:
                name_str = 'Metagame Cards.csv'
                
            content_str = 'Name;Type;Count;Total\n'
            content_str += '\n'.join([';'.join([str(node[key]) for key in ['label', 'Card Type', 'Number of Decks', 'Number of Copies']]) for node in graph_data['nodes'] if not node['hidden']])
            return dict(content = content_str, filename = name_str)
        
        @app.callback(
            [Output('graph', 'data'),
             Output('color-legend-popup', 'children')],
            [Input('select_format', 'value'),
             Input('nbhd_type', 'value'),
             Input('search_graph', 'value'),
             Input('color_nodes', 'value'),
             Input('size_nodes', 'value'),
             Input('graph', 'selection')],
            [State('graph', 'data')]
        )
        def setting_pane_callback(format_selection,
                                  nbhd_type,
                                  search_text,
                                  color_nodes_value,
                                  size_nodes_value,
                                  selection,
                                  graph_data):
            #fetch the id of the option which triggered the callback
            ctx = dash.callback_context
            if ctx.triggered:
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                if input_id == 'select_format':
                    graph_data = self._callback_format_select(graph_data, format_selection)
                if input_id == 'nbhd_type':
                    self.nbhd_type = nbhd_type
                    graph_data = self._callback_show_nbhd(graph_data)
                if input_id == 'search_graph':
                    graph_data = self._callback_search_graph(graph_data, search_text)
                if input_id == 'color_nodes':
                    graph_data, self.node_value_color_mapping = self._callback_color_nodes(graph_data, color_nodes_value)
                if input_id == 'size_nodes':
                    self.size_nodes_option = size_nodes_value
                    graph_data = self._callback_size_nodes(graph_data)
                if input_id == 'graph':
                    self.selection = selection
                    graph_data = self._callback_show_nbhd(graph_data)
                
            color_popover_legend_children = self.get_color_popover_legend_children(self.node_value_color_mapping, self.edge_value_color_mapping)
            return [graph_data, color_popover_legend_children]
        
        return app
        
    def get_color_popover_legend_children(self, node_value_color_mapping = {}, edge_value_color_mapping = {}):
        popover_legend_children = []
        def create_legends_for(title='Node', legends={}):
            _popover_legend_children = [dbc.PopoverHeader(f"{title} legends")]
            if len(legends) > 0:
                for key, value in legends.items():
                    _popover_legend_children.append(
                        create_color_legend(key, value))
            else:
                _popover_legend_children.append(dbc.PopoverBody(f"No {title.lower()}s colored!"))
            
            return _popover_legend_children
        
        popover_legend_children.extend(create_legends_for('Node', node_value_color_mapping))
        popover_legend_children.extend(create_legends_for('Edge', edge_value_color_mapping))
        return popover_legend_children
                

mavis = Mavis()
# =============================================================================
#igor.visualizer.load()
#app = igor.visualizer.plot()
#server = app.server
if __name__=='__main__':
    mavis.app.run_server(debug=True, port='5000')