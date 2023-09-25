# -*- coding: utf-8 -*-
"""
Created on Wed Dec  8 23:21:28 2021

Adapted from the Jaal package.
"""
import visdcc
from dash import dcc, html
import dash_bootstrap_components as dbc
import pandas as pd

# Constants

# default node and egde color
DEFAULT_COLOR = '#97C2FC'
DARK_GREY = '#555555'
LIGHT_GREY = '#CCCCCC'
WHITE = "#FFFFFF"
BLACK = "#000000"
SELECTED_BUTTON_STYLE = {
                            'margin': 4, 
                            'padding':4, 
                            'backgroundColor': DARK_GREY,
                            'color': WHITE,
                        }
UNSELECTED_BUTTON_STYLE = {
                            'margin': 4, 
                            'padding':4, 
                            'backgroundColor': LIGHT_GREY,
                            'color': BLACK,
                        }
SELECTED_BUTTON_COLOR = DARK_GREY
SELECTED_TEXT_COLOR = WHITE
UNSELECTED_BUTTON_COLOR = LIGHT_GREY
UNSELECTED_TEXT_COLOR = BLACK

#--------------
# default node and edge size
DEFAULT_NODE_SIZE = 7
DEFAULT_NODE_COLOR = DEFAULT_COLOR
DEFAULT_EDGE_WIDTH = 1
DEFAULT_EDGE_COLOR = DEFAULT_COLOR

# Taken from https://stackoverflow.com/questions/470690/how-to-automatically-generate-n-distinct-colors
KELLY_COLORS_HEX = [
    "#FFB300", # Vivid Yellow
    "#803E75", # Strong Purple
    "#FF6800", # Vivid Orange
    "#A6BDD7", # Very Light Blue
    "#C10020", # Vivid Red
    "#CEA262", # Grayish Yellow
    "#817066", # Medium Gray

    # The following don't work well for people with deficient color vision
    "#007D34", # Vivid Green
    "#F6768E", # Strong Purplish Pink
    "#00538A", # Strong Blue
    "#FF7A5C", # Strong Yellowish Pink
    "#53377A", # Strong Violet
    "#FF8E00", # Vivid Orange Yellow
    "#B32851", # Strong Purplish Red
    "#F4C800", # Vivid Greenish Yellow
    "#7F180D", # Strong Reddish Brown
    "#93AA00", # Vivid Yellowish Green
    "#593315", # Deep Yellowish Brown
    "#F13A13", # Vivid Reddish Orange
    "#232C16", # Dark Olive GreenW
    ]

DEFAULT_OPTIONS = {
    'height': '600px',
    'width': '100%',
    'interaction':{'hover': True},
    # 'edges': {'scaling': {'min': 1, 'max': 5}},
    'physics':{'solver': 'forceAtlas2Based',
               'stabilization':{'iterations': 1},
               'barnesHut':{'damping': 0.4,
                            'centralGravity': 0.2},
               'repulsion':{'damping': 0.3,
                            'springConstant': 0.2},
               'forceAtlas2Based': {'springLength':1,
                                    'springConstant': 0.09,
                                    'damping': 0.6,
                                    'centralGravity':0.03}}
}

DEFAULT_FLEX_ROW_STYLE = {'display': 'flex', 
                          'flex-direction': 'row', 
                          'justify-content': 'center', 
                          'align-items': 'center'}

def get_categorical_features(df_, blacklist_features=['shape', 'label', 'id', 'deck_count', 'total_copies', 'true_color', 'lighten']):
    """Identify categorical features for edge or node data and return their names
        Cardinality should be within 'unique_limit'
    """
    
    cat_features = ['None'] + df_.columns[(df_.dtypes == 'object')].tolist()
    try:
        #try to remove irrelevant cols
        for col in blacklist_features:
            cat_features.remove(col)
    except:
        pass
        
    return cat_features

def get_numerical_features(df_, unique_limit=20):
    """Identify numerical features for edge or node data and return their names"""
    
    #supported numerical cols
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    #identify numerical features
    numeric_features = ['None'] + df_.select_dtypes(include=numerics).columns.tolist()
    #try to remove blacklist cols (for nodes)
    try:
        numeric_features.remove('size')
    except:
        pass
    
    return numeric_features

def compute_scaling_vars_for_numerical_cols(df):
    """Identify and scale numerical cols"""
    # identify numerical cols
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    numeric_cols = df.select_dtypes(include=numerics).columns.tolist()
    # var to hold the scaling function
    scaling_vars = {}
    # scale numerical cols
    for col in numeric_cols:
        minn, maxx = df[col].min(), df[col].max()
        scaling_vars[col] = {'min': minn, 'max': maxx} 
    # return
    return scaling_vars

def get_node_and_edge_scaling_vars(data):
    scaling_vars = {'node': None, 'edge': None}
    scaling_vars['node'] = compute_scaling_vars_for_numerical_cols(pd.DataFrame(data['nodes']))
    scaling_vars['edge'] = compute_scaling_vars_for_numerical_cols(pd.DataFrame(data['edges']))
    return scaling_vars
    
def get_options(directed, opts_args):
    opts = DEFAULT_OPTIONS.copy()
    opts['edges'] = { 'arrows': { 'to': directed } }
    if opts_args is not None:
        opts.update(opts_args)
    return opts

def get_distinct_colors(n):
    """Return (at most 20) distinct colors."""
    if n > len(KELLY_COLORS_HEX):
        raise ValueError("Unable to provide more than 20 unique colors.")
    return KELLY_COLORS_HEX[:n]

def create_row(children, style=DEFAULT_FLEX_ROW_STYLE):
    return dbc.Row(children,
                   style=style,
                   className="column flex-display")

def create_color_legend(text, color):
    """Individual row for the color legend"""
    
    return create_row([
        html.Div(style={'width': '10px', 'height': '10px', 'margin-top': '5px', 'background-color': color}),
        html.Div(text, style={'padding-left': '10px', 'margin-bottom': 3})
        ], {'align-content': 'center', 'justify-content':'flex-start', 'margin': 2, 'margin-left': 7})

search_form = dbc.FormGroup([
    dbc.Input(type='Search', id='search_graph', placeholder='Search node in graph...'),
    dbc.FormText(
        'Show the node you are looking for',
        color='secondary',
    ),
])

filter_node_form = dbc.FormGroup([
    dbc.Textarea(id="filter_nodes", placeholder="Enter filter node query here..."),
    dbc.FormText(
        html.P([
            "Filter on nodes properties by using ",
            html.A("Pandas Query syntax",
            href="https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.query.html"),
        ]),
        color="secondary",
    ),
])

filter_edge_form = dbc.FormGroup([
    dbc.Textarea(id="filter_edges", placeholder="Enter filter edge query here..."),
    dbc.FormText(
        html.P([
            "Filter on edges properties by using ",
            html.A("Pandas Query syntax",
            href="https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.query.html"),
        ]),
        color="secondary",
    ),
])

def get_select_form_layout(id, options, label, description, default = None):
    """Creates a select (dropdown) form with provided details
    
    Parameters
    ------------
    id: str
        id of the form
    options: list
        options to show
    label: str
        label of the select dropdown bar
    description: str
        long text detail of the setting
    """
    
    return dbc.FormGroup([
        dbc.InputGroup([
            dbc.InputGroupAddon(label, addon_type='append'),
            dbc.Select(id=id,
                       options=options,
                       value = default
            ),])
        ,])

def get_app_layout(graph_data, formats, color_legends=[], directed=False, vis_opts = None):
    """Create and return the layout of the app
        
    Parameters
    -------------
    graph_data: dict{nodes, edges}
        network data in fromat of visdcc
    """
    
    #Step 1-2: find categorical features of nodes and edges
    cat_node_features = get_categorical_features(pd.DataFrame(graph_data['nodes']).drop(columns=['true_color', 'color', 'visibility', 'lighten']))
    cat_edge_features = get_categorical_features(pd.DataFrame(graph_data['edges']).drop(columns=['color']), ['color', 'from', 'to', 'id', 'visibility', 'lighten'])
    #Step 3-4: Get numerical features of nodes and edges
    num_node_features = get_numerical_features(pd.DataFrame(graph_data['nodes']))
    num_edge_features = get_numerical_features(pd.DataFrame(graph_data['edges']))
    #Step 5: create and return the layout
    return html.Div([
            create_row(html.Img(src='https://i.imgur.com/7sqCsZt.png', width='200px')),
            create_row([
                dbc.Col([
                    #setting panel
                    dbc.Form([
                        dbc.Collapse([
                            #---format selection---
                            create_row([
                                html.H6('Select Format'), #heading
                            ], {**DEFAULT_FLEX_ROW_STYLE, 'margin-left': 0, 'margin-right': 0, 'justify-content': 'space-between'}),
                            dbc.Collapse([
                                html.Hr(className='my-2'),
                                get_select_form_layout(
                                    id='select_format',
                                    options=[{'label': format_name, 'value': format_name} for format_name in formats],
                                    label='Format Selection',
                                    description='Select the metagame format you would like to see.',
                                    default = 'All'
                                ),
                            ], id='sector-show-toggle', is_open=True),
                            #---neighbourhood section---
                            create_row([
                                html.H6('Neighbourhood'), #heading
                            ], {**DEFAULT_FLEX_ROW_STYLE, 'margin-left': 0, 'margin-right': 0, 'justify-content': 'space-between'}),
                            dbc.Collapse([
                                html.Hr(className='my-2'),
                                get_select_form_layout(
                                    id='nbhd_type',
                                    options=[{'label': 'None', 'value': 'None'},
                                             {'label': 'Direct Neighbours', 'value': 'neighbours'},
                                             {'label': '2-Neighbours', 'value': '2-neighbours'}],
                                    label='Neighbourhood Type',
                                    description='Select the type of neighbourhood you would like to see when you select a card.',
                                    default = 'None'
                                ),
                            ], id='nbhd-show-toggle', is_open=True),
                            
                            #---search section---
                            html.H6("Search"),
                            html.Hr(className='my-2'),
                            search_form,
                        ], id='igor-show-toggle', is_open=True),
                        #---color section---
                        create_row([
                            html.H6('Color'), # heading
                            html.Div([
                                dbc.Button('Legends', 
                                           id='color-legend-toggle', 
                                           outline=True, 
                                           color='secondary', 
                                           size='sm',
                                           style={'margin': 4}), #legend
                            ]),
                            #add the legends popup
                            dbc.Popover(
                                children=color_legends,
                                id='color-legend-popup', is_open=False, target='color-legend-toggle',
                                style = {'width': 200,
                                         'justify-content': 'flex-start'}
                            ),
                        ], {**DEFAULT_FLEX_ROW_STYLE, 'margin-left': 0, 'margin-right': 0, 'justify-content': 'space-between'}),
                        create_row([
                            html.Div([
                                get_select_form_layout(
                                    id='color_nodes',
                                    options=[{'label': opt, 'value': opt} for opt in cat_node_features],
                                    label='Color nodes by',
                                    description='Select the cattegorical node proprty to color nodes by'
                                ),
                            ])
                        ], {**DEFAULT_FLEX_ROW_STYLE, 'margin-left': 0, 'margin-right': 0, 'margin-top':4, 'justify-content': 'space-between'}),
                          
                        #---size section---
                        create_row([
                            html.H6('Size'), #heading
                        ], {**DEFAULT_FLEX_ROW_STYLE, 'margin-left': 0, 'margin-right': 0, 'justify-content': 'space-between'}),
                        create_row([
                                get_select_form_layout(
                                    id='size_nodes',
                                    options=[{'label':opt, 'value': opt} for opt in num_node_features],
                                    label='Size nodes by',
                                    description='Select the numerical node property to size nodes by'
                            )
                        ], {**DEFAULT_FLEX_ROW_STYLE, 'margin-left': 0, 'margin-right': 0, 'margin-top':4, 'justify-content': 'space-between'}),
                        dbc.Collapse([
                            create_row([
                                html.H6('Controls'), #heading
                                html.Div([
                                    dbc.Button('Start', id ='start-button', outline=True, color='secondary', size='sm'),
                                    dbc.Button('Previous', id='previous-button', outline=True, color='secondary', size='sm'), #legend
                                    dbc.Button('Next', id='next-button', outline=True, color='secondary', size='sm'), #legend
                                    dbc.Button('End', id='end-button', outline=True, color='secondary', size='sm')
                                ]),
                                html.Div([
                                    dcc.Interval(id='interval1', interval=1000, n_intervals=0)
                                ])
                            ], {**DEFAULT_FLEX_ROW_STYLE, 'margin-left': 0, 'margin-right': 0, 'justify-content': 'space-between'}),
                            create_row([
                                html.Div([
                                    html.H1(id='label1', children='')
                                ])
                            ], {**DEFAULT_FLEX_ROW_STYLE, 'margin-left': 30, 'margin-right': 0, 'justify-content': 'space-between'}),
                        ], id='ichabod-show-toggle', is_open=False),
                        #---export section---
                        create_row([
                            html.H6('Export'), #heading
                            html.Div([
                                dbc.Button('Export CSV', id='export-csv-button', outline=True, color='secondary', size='sm'), #legend
                                #dbc.Button('Snapshot', id='snapshot-button', outline=True, color='secondary', size='sm'), #legend
                            ]),
                        ], {**DEFAULT_FLEX_ROW_STYLE, 'margin-left': 0, 'margin-right': 0, 'justify-content': 'space-between'}),
                        dcc.Download(id='export-csv'),                        
                    ], className='card', style={'padding':'5px', 'background':'#e5e5e5'}),
                ], width=3, style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}),
                # graph
                dbc.Col(
                    visdcc.Network(
                        id = 'graph',
                        selection = {'nodes':[], 'edges':[]},
                        data = graph_data,
                        options = get_options(directed, vis_opts)),
                    width=9)
                ])
            ])