# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from plotly import subplots
from global_data import tree_data_pgn, tree_data_fen, game_data_pgn, game_data_fen, config_data

from server import app
from miniboard import node_info

import time

RIGHT_TITLE_SIZE = 15
FONT_SIZE = 13
FONT_COLOR = '#2a3f5f'
GRID_COLOR = 'rgba(127,127,127, 0.25)'
PV_COLOR = 'rgb(23,178,207)'
BRANCH_COLORS = ['rgb(31,119,180)', 'rgb(255,127,14)']
PLOT_BACKGROUND_COLOR = 'rgb(255,255,255)'
BAR_COLOR = 'rgb(31,119,180)'
EDGE_COLOR = 'black'
HOVER_LABEL_COLOR = 'white'
ROOT_NODE_COLOR = 'red'
BEST_MOVE_COLOR = 'rgb(178,34,34)'
MOVED_PIECE_COLOR = 'rgb(210,105,30)'
MARKER_SIZE = 5.0
FONT_FAMILY = 'monospace'
GRAPH_WIDTH = 84
PGN_WIDTH = 100 - GRAPH_WIDTH
MONO_FONT_FAMILY = 'BundledDejavuSansMono'
HOVER_FONT_SIZE = 15

NODE_LIMIT_FOR_WEBGL = 2000 #switch to WEBGL above certain nodes


def empty_figure():
    figure = subplots.make_subplots(rows=1, cols=2,
                                    specs=[[{}, {}]],
                                    shared_xaxes=True,
                                    shared_yaxes=False,
                                    vertical_spacing=0.001)
    layout = go.Layout(
        annotations=[
            dict(
                x=1.025,
                y=0.5,
                showarrow=False,
                text='Nodes per depth',
                xref='paper',
                yref='paper',
                textangle=90,
                font=dict(family=MONO_FONT_FAMILY, size=RIGHT_TITLE_SIZE, color=FONT_COLOR)
            ),
        ],
        xaxis={'title': 'Visit distribution',
               'range': [0, 1],
               'zeroline': False,
               'showgrid': False,
               'domain': [0.0, 0.91],
               'tickvals': [],
               'ticktext': []},
        yaxis={'title': 'Depth',
               'range': [-1, 10],
               'ticktext': [str(i) for i in range(10)],
               'tickvals': [i for i in range(10)][::-1],
               'zeroline': False,
               'showgrid': True,
               'gridcolor': GRID_COLOR},
        yaxis2={'title': '',
                'range': [0, 1],
                'showticklabels': True,
                'side': 'left',
                'ticktext': [0],
                'tickvals': [i for i in range(10)][::-1]},
        xaxis2={'zeroline': False,
                'showgrid': False,
                'showticklabels': False,
                'domain': [0.93, 1.0],
                'range': [-1, 10]},
        hovermode='closest',
        plot_bgcolor=PLOT_BACKGROUND_COLOR,
        margin={'t': 0, 'b': 0}
    )
    figure['layout'].update(layout)
    return(figure)


def get_data(data, visible):
    start = time.time()
    points_odd, node_text_odd, node_ids_odd = [], [], []
    points_even, node_text_even, node_ids_even = [], [], []
    points_root, node_text_root, node_ids_root = [], [], []
    x_edges, y_edges = [], []
    x_edges_pv, y_edges_pv = [], []
    for node_id in data:
        node = data[node_id]
        node_state_info = node['visible'].get(visible)
        if node_state_info is None: # node is not visible for this state
            continue
        type, edge_type = node_state_info['type']
        node_metrics = node_state_info['metric']

        point = node['point']
        x_parent, y_parent = node['parent']
        node_text = node['miniboard'] + node_metrics

        if type == 'odd':
            points_odd.append(point)
            node_text_odd.append(node_text)
            node_ids_odd.append(node_id)
        elif type == 'even':
            points_even.append(point)
            node_text_even.append(node_text)
            node_ids_even.append(node_id)
        elif type == 'root':
            points_root.append(point)
            node_text_root.append(node_text)
            node_ids_root.append(node_id)
        if edge_type == 'pv':
            x_edges_pv += [point[0], x_parent, None]
            y_edges_pv += [point[1], y_parent, None]
        else:
            x_edges += [point[0], x_parent, None]
            y_edges += [point[1], y_parent, None]

    x_odd, y_odd = zip(*points_odd) if points_odd != [] else ([], [])
    x_even, y_even = zip(*points_even) if points_even != [] else ([], [])
    x_root, y_root = zip(*points_root) if points_root != [] else ([], [])

    print('Tree plot data fetched in', time.time() - start, 's')


    return (x_odd, y_odd, node_text_odd, node_ids_odd,
            x_even, y_even, node_text_even, node_ids_even,
            x_root, y_root, node_text_root, node_ids_root,
            x_edges, y_edges,
            x_edges_pv, y_edges_pv,)

def tree_graph():
    graph_component = html.Div(style={'height': '100%', 'width': '100%'})
    loading_component = html.Div(dcc.Loading(children=[html.Div(id='loading_trigger', style={'display': 'none'})], style={'flex': 1}),
                                 style={'height': '5%', 'overflow': 'auto', 'display': 'flex', 'flexDirection': 'column'})
    config_info = html.Div(id='config_info', style={'textAlign': 'center', 'height': '5%', 'overflowY': 'auto'})
    graph_container = html.Div(id='graph-container',
                           children=[html.Div( children=[
                                     dcc.Graph(id='graph',
                                               figure={'layout': {'title': ''}},
                                               style={'height': '100%', 'marginTop': '0'},
                                               config={'displayModeBar': False},
                                               clear_on_unhover=True,
                                               ), node_info('12.5%', '12.5%', '0', '0'),
                           ],
                               style={'height': '87.5%',
                                      'marginBottom': '25px',
                                      'position': 'relative',
                                      #'border': '5px solid red',
                                      }),
                                     html.Div(dcc.Slider(id='slider1',
                                                         min=0,
                                                         value=0,
                                                         step=None,
                                                         ),
                                              style={'height': '12.5%', 'width': '95%', 'margin': 'auto'}),#updatemode='drag'
                                     html.Div(id='hidden-div-slider-state', style={'display': 'none'}, children='test')
                                     ],
                           style={'height': '90%', 'width': '100%', 'float': 'left'}
                           )
    graph_component.children = [loading_component, config_info, graph_container]
    return(graph_component)



@app.callback(
    [Output('generate-data-button', 'title'),
    Output('loading_trigger', 'children')],
    [Input('generate-data-button', 'n_clicks_timestamp'),
     Input('generate-data-selected-button', 'n_clicks_timestamp'),
     ],
    [State('slider1', 'marks'),
     State('move-table', 'active_cell'),
     State('nodes-mode-selector', 'value'),
     State('nodes_input', 'value'),
     State('net-mode-selector', 'value'),
     State('net_selector', 'value'),
     State('position-mode-selector', 'value')]
)
def generate_data(n_clicks_all_timestamp, n_clicks_selected_timestamp, marks, active_cell, nodes_mode, global_nodes, net_mode, global_net, position_mode):
    if n_clicks_selected_timestamp is None:
        n_clicks_selected_timestamp = -1
    if n_clicks_all_timestamp is None:
        n_clicks_all_timestamp = -1
    if n_clicks_all_timestamp == -1 and n_clicks_selected_timestamp == -1:
        return(dash.no_update, dash.no_update)

    if position_mode == 'pgn':
        tree_data = tree_data_pgn
        game_data = game_data_pgn
    else:
        tree_data = tree_data_fen
        game_data = game_data_fen

    data = game_data.data
    if data is None:
        return ("No positions to analyze", dash.no_update)

    is_analyze_selected = False
    if n_clicks_selected_timestamp > n_clicks_all_timestamp:
        is_analyze_selected = True
        row_index = active_cell['row']
        position_indices = [data[row_index]['ply']]
    else:
        position_indices = [row['ply'] for row in data]
    nr_of_positions = len(position_indices)

    #net = '/home/jusufe/leelas/graph_analysis3/nets60T/weights_run1_62100.pb.gz'
    #engine = '/home/jusufe/lc0_farmers/build/release/lc0'# '/home/jusufe/lc0_test4/build/release/lc0'
    #tree_data.args = [engine, '--weights=' + net]

    board = game_data.board
    if not is_analyze_selected:
        tree_data.G_dict = {}
        tree_data.merged_graphs = {}
        tree_data.data = {}
        tree_data.heatmap_data_for_moves = {}
        tree_data.heatmap_data_for_board_states = {}
    else:
        for position_id in position_indices:
            tree_data.G_dict.pop(position_id, None)  # clear graph data for this position
            tree_data.merged_graphs.pop(position_id, None)
            tree_data.heatmap_data_for_moves.pop(position_id, None)
            tree_data.heatmap_data_for_board_states.pop(position_id, None)
    for config_i in range(len(marks)):
        nodes = config_data.get_nodes(config_i, nodes_mode, global_nodes)
        for position_id in position_indices:
            game_data.set_board_position(position_id)
            if net_mode != ['global']:
                global_net = None
            configurations = config_data.get_configurations(config_i, global_net)
            tree_data.run_search(position_id, configurations, board, nodes)

    for position_id in position_indices:
        game_data.set_board_position(position_id)
        fen = board.fen()
        tree_data.create_data(position_id, fen)
    if is_analyze_selected:
        return('', str(nr_of_positions))
    return(f'All {str(nr_of_positions)} positions analyzed', str(nr_of_positions))

@app.callback(
    [Output('graph', 'figure'),
     Output('config_info', 'children')],
    [Input('slider1', 'value'),
     Input('move-table', 'active_cell'),
     Input('net-mode-selector', 'value'),
     Input('config-table-dummy-div', 'children')],
    [State('net_selector', 'value'),
     State('position-mode-selector', 'value')]
)
def update_data(selected_value, active_cell, net_mode, config_changed, global_net, position_mode):
    if position_mode == 'pgn':
        tree_data = tree_data_pgn
        game_data = game_data_pgn
    else:
        tree_data = tree_data_fen
        game_data = game_data_fen

    if net_mode != ['global']:
        global_net = None
    configurations = config_data.get_configurations(selected_value, global_net, only_non_default=True)
    tooltip = ', '.join([f'{option}={configurations[option]}' for option in configurations])

    if active_cell is None or game_data.data is None:
        return (empty_figure(), tooltip)
    else:
        position_id = active_cell['row']
        position_id = game_data.data[position_id]['ply']

    #Show empty graph if position is not yet analyzed
    if position_id not in tree_data.data:
        return(empty_figure(), tooltip)
    data = tree_data.data[position_id]
    x_odd, y_odd, node_text_odd, node_ids_odd,\
    x_even, y_even, node_text_even, node_ids_even,\
    x_root, y_root, node_text_root, node_ids_root,\
    x_edges, y_edges, x_edges_pv, y_edges_pv = get_data(data, selected_value)

    #if there is no root node, then slider is set to value that has not been analyzed yet
    if x_root == []:
        return(empty_figure(), tooltip)

    if len(x_odd) + len(x_even) + 1 >= NODE_LIMIT_FOR_WEBGL:
        scatter = go.Scattergl#go.Scattergl #go.Scatter
    else:
        scatter = go.Scatter
    trace_node_odd = scatter(x=x_odd,
                             y=y_odd,
                             mode='markers',
                             marker={'color': BRANCH_COLORS[1], 'symbol': "circle", 'size': MARKER_SIZE},
                             customdata=node_ids_odd,
                             #text=node_text_odd,
                             hovertext=node_text_odd,
                             hoverinfo='text',
                             textfont={"family": MONO_FONT_FAMILY},
                             hoverlabel=dict(font=dict(family=MONO_FONT_FAMILY, size=HOVER_FONT_SIZE), bgcolor=HOVER_LABEL_COLOR),
                             showlegend=False
                             )
    trace_node_even = scatter(x=x_even,
                              y=y_even,
                              mode='markers',
                              marker={'color': BRANCH_COLORS[0], 'symbol': "circle", 'size': MARKER_SIZE},
                              customdata=node_ids_even,
                              hovertext=node_text_even,
                              hoverinfo='text',
                              textfont={"family": MONO_FONT_FAMILY},
                              hoverlabel=dict(font=dict(family=MONO_FONT_FAMILY, size=HOVER_FONT_SIZE), bgcolor=HOVER_LABEL_COLOR),
                              showlegend=False
                              )

    trace_node_root = scatter(x=x_root,
                              y=y_root,
                              mode='markers',
                              marker={'color': ROOT_NODE_COLOR, 'symbol': "circle", 'size': MARKER_SIZE},
                              customdata=node_ids_root,
                              hovertext=node_text_root,
                              hoverinfo='text',
                              textfont={"family": MONO_FONT_FAMILY},
                              hoverlabel=dict(font=dict(family=MONO_FONT_FAMILY, size=HOVER_FONT_SIZE), bgcolor=HOVER_LABEL_COLOR),
                              showlegend=False
                              )

    trace_edge = scatter(x=x_edges,
                         y=y_edges,
                         mode='lines',
                         line=dict(color=EDGE_COLOR, width=0.5),
                         showlegend=False,
                         hoverinfo='skip'
                         )

    trace_edge_pv = scatter(x=x_edges_pv,
                            y=y_edges_pv,
                            mode='lines',
                            line=dict(color=PV_COLOR, width=1.75),
                            showlegend=False,
                            hoverinfo='skip'
                            )

    traces = [trace_edge,
              trace_edge_pv,
              trace_node_odd,
              trace_node_even,
              trace_node_root]

    x_hist, y_hist = tree_data.data_depth[position_id][selected_value]

    trace_depth_histogram = go.Bar(x=y_hist, y=x_hist, orientation='h',
                                   showlegend=False, hoverinfo='skip',
                                   marker=dict(color=BAR_COLOR))

    x_range = tree_data.x_range[position_id]
    y_range = tree_data.y_range[position_id]
    y_tick_values = tree_data.y_tick_values[position_id]
    y_tick_labels = tree_data.y_tick_labels[position_id]

    #pad labels for nice alignment
    y_hist_labels = ['0' for _ in range(len(y_tick_labels) - len(y_hist))] + list(map(str, y_hist))
    max_y2_label_len = max(map(len, y_hist_labels))
    y2_tick_labels = [label.rjust(max_y2_label_len, ' ') for label in y_hist_labels]

    y2_range = tree_data.y2_range[position_id]
    x_tick_labels = tree_data.x_tick_labels[position_id][selected_value]
    x_tick_values = tree_data.x_tick_values[position_id]


    layout = go.Layout(#title=dict(text='Leela tree Visualization', x=0.5, xanchor="center"),
                       annotations=[
                                    dict(
                                        x=1.025,
                                        y=0.5,
                                        showarrow=False,
                                        text='Nodes per depth',
                                        xref='paper',
                                        yref='paper',
                                        textangle=90,
                                        font=dict(family=MONO_FONT_FAMILY, size=RIGHT_TITLE_SIZE, color=FONT_COLOR)
                                    ),
                                ],
                       xaxis={'title': 'Visit distribution',
                              'range': x_range,
                              'zeroline': False,
                              'showgrid': False,
                              'domain': [0.0, 0.91],
                              'tickvals': x_tick_values,
                              'ticktext': x_tick_labels},
                       yaxis={'title': 'Depth',
                              'range': y_range,
                              'ticktext': y_tick_labels,
                              'tickvals': y_tick_values,
                              'zeroline': False,
                              'showgrid': True,
                              'gridcolor': GRID_COLOR},
                       yaxis2={'title': '',
                               'range': y_range,
                               'showticklabels': True,
                               'side': 'left',
                               'ticktext': y2_tick_labels,
                               'tickvals': y_tick_values},
                       xaxis2={'zeroline': False,
                               'showgrid': False,
                               'showticklabels': False,
                               'domain': [0.93, 1.0],
                               'range': y2_range},
                       hovermode='closest',
                       plot_bgcolor=PLOT_BACKGROUND_COLOR,
                       #height=900,
        margin={'t': 0, 'b': 0}
                       )
    figure = subplots.make_subplots(rows=1, cols=2,
                                    specs=[[{}, {}]],
                                    shared_xaxes=True,
                                    shared_yaxes=False,
                                    vertical_spacing=0.001)
    for trace in traces:
        figure.append_trace(trace, 1, 1)

    figure.append_trace(trace_depth_histogram, 1, 2)
    figure['layout'].update(layout)

    return(figure, tooltip)

@app.callback(
    Output('hidden-div-slider-state', 'children'),
    [Input('slider1', 'value'),
     Input('generate-data-button', 'title')],
    [State('position-mode-selector', 'value')])
def update_game_evals(visible, title, position_mode):
    if position_mode == 'pgn':
        tree_data = tree_data_pgn
        game_data = game_data_pgn
    else:
        tree_data = tree_data_fen
        game_data = game_data_fen

    Q_values = []
    W_values = []
    D_values = []
    L_values = []
    M_values = []
    if game_data.data is None:
        return(dash.no_update)

    for row in game_data.data:
        position_id = row['ply']
        if position_id not in tree_data.data: #position not yet evaluated
            Q, W, D, L, M = None, None, None, None, None
        elif visible not in tree_data.data[position_id]['root']['visible']: #engine config set not yet evaluated
            Q, W, D, L, M = None, None, None, None, None
        else:
            root = tree_data.data[position_id]['root']
            evaluation = root['visible'][visible]['eval']
            Q = evaluation['Q']
            W = evaluation['W']
            D = evaluation['D']
            L = evaluation['L']
            M = evaluation['M']

            #invert W and L for black
            turn = game_data.get_value_by_position_id('turn', position_id)
            if not turn:
                W = 100 - W - D
                L = 100 - L - D
        Q_values.append(Q)
        W_values.append(W)
        D_values.append(D)
        L_values.append(L)
        M_values.append(M)
    game_data.set_column('Q', Q_values)
    game_data.set_column('W', W_values)
    game_data.set_column('D', D_values)
    game_data.set_column('L', L_values)
    game_data.set_column('M', M_values)
    game_data.data_previous = game_data.data
    return(str(visible))
