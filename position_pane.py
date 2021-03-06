# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_table
import dash_html_components as html
import io
import chess
import chess.svg
import python_chess_customized_svg as svg
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

import chess.pgn
import base64
from server import app

from global_data import tree_data_pgn, tree_data_fen, game_data_fen, game_data_pgn
from dash_table.Format import Format, Symbol, Scheme

import plottools as pt

from colors import rgb_adjust_saturation

from quit import quit_button
import copy

COMPONENT_WIDTH = '98%'
WHITE_WIN_COLOR = 'rgb(255, 255, 255)'
DRAW_COLOR ='rgb(184, 184, 184)'
BLACK_WIN_COLOR = 'rgb(0, 0, 0)'
SELECTED_ROW_COLOR = 'rgba(23,178,207,0.5)'
BAR_LINE_COLOR = 'rgb(100, 100, 100)'
WHITE_WIN_BAR_LINE_COLOR = BAR_LINE_COLOR#'rgb(0, 0, 0)'
DRAW_BAR_LINE_COLOR = BAR_LINE_COLOR#'rgb(0, 0, 0)'
BLACK_WIN_BAR_LINE_COLOR = BAR_LINE_COLOR#'rgb(255, 255, 255)'
BAR_LINE_WIDTH = 1
RELATIVE_HEIGHT_OF_SCORE_BAR = "7.5%"
SHOW_BOARD_COORDINATES = False

FEN_PGN_COMPONENT_RELATIVE_HEIGHT = "20%"#"13.5%"

ARROW_COLORS = {
    'p': (183, 0, 255), #purple
    'n': (0, 166, 255),
    'q': (255, 0, 0),
    'ml_low': (255, 51, 153),
    'ml_high': (255, 51, 153)}

PGN_MODE_COLUMNS = [#{"name": '', "id": 'dummy_left'},
    {"name": 'ply', "id": 'ply'},
    {"name": 'move', "id": 'move'},
    {"name": 'Q', "id": 'Q', 'type': 'numeric', 'format': Format(precision=3, scheme=Scheme.fixed)},
    {"name": 'W-%', "id": 'W', 'type': 'numeric', 'format': Format(precision=0, symbol=Symbol.yes, symbol_suffix='%', scheme=Scheme.fixed)},
    {"name": 'D-%', "id": 'D', 'type': 'numeric', 'format': Format(precision=0, symbol=Symbol.yes, symbol_suffix='%', scheme=Scheme.fixed)},
    {"name": 'B-%', "id": 'L', 'type': 'numeric', 'format': Format(precision=0, symbol=Symbol.yes, symbol_suffix='%', scheme=Scheme.fixed)},
    {"name": 'ML', "id": 'M', 'type': 'numeric', 'format': Format(precision=1, scheme=Scheme.fixed)},
    {"name": '', "id": 'dummy_right'},
]

FEN_MODE_COLUMNS = [
    {"name": 'Id', "id": 'ply'},
    {"name": 'turn', "id": 'move'},
    {"name": 'Q', "id": 'Q', 'type': 'numeric', 'format': Format(precision=3, scheme=Scheme.fixed)},
    {"name": 'W-%', "id": 'W', 'type': 'numeric', 'format': Format(precision=0, symbol=Symbol.yes, symbol_suffix='%', scheme=Scheme.fixed)},
    {"name": 'D-%', "id": 'D', 'type': 'numeric', 'format': Format(precision=0, symbol=Symbol.yes, symbol_suffix='%', scheme=Scheme.fixed)},
    {"name": 'B-%', "id": 'L', 'type': 'numeric', 'format': Format(precision=0, symbol=Symbol.yes, symbol_suffix='%', scheme=Scheme.fixed)},
    {"name": 'ML', "id": 'M', 'type': 'numeric', 'format': Format(precision=1, scheme=Scheme.fixed)},
    {"name": '', "id": 'dummy_right'}
]

PGN_COMPONENT_STYLE = {
                'height': '100%',
                'width': '100%',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'position': 'absolute',
                'left': 0,
                'display': 'flex',
                'flexDirection': 'column',
            }
FEN_COMPONENT_STYLE = {'position': 'absolute', 'left': 0, 'height': '100%', 'width': '97%'}#97% width since firefox sux and overflows with 100%


def get_score_bar_figure(W, D, B):
    W = go.Bar(name='White win-%', y=[''], x=[W],
               text=[f'{int(round(W))}%'],
               textposition='auto',
               hoverinfo='x',
               orientation='h',
               marker=dict(color=WHITE_WIN_COLOR,
                           line=dict(color=WHITE_WIN_BAR_LINE_COLOR,
                                     width=BAR_LINE_WIDTH)))
    D = go.Bar(name='Draw-%', y=[''], x=[D],
               text=[f'{int(round(D))}%'],
               textposition='auto',
               hoverinfo='x',
               orientation='h',
               marker=dict(color=DRAW_COLOR,
                           line=dict(color=DRAW_BAR_LINE_COLOR,
                                     width=BAR_LINE_WIDTH)))
    B = go.Bar(name='Black win-%', y=[''], x=[B],
               text=[f'{int(round(B))}%'],
               textposition='auto',
               hoverinfo='x',
               orientation='h',
               marker=dict(color=BLACK_WIN_COLOR,
                           line=dict(color=BLACK_WIN_BAR_LINE_COLOR,
                                     width=BAR_LINE_WIDTH)))
    fig = go.Figure(data=[W, D, B])

    xaxis = {'range': [0,100],
             'showgrid': False,
             #'ticks': 'outside',
             'showticklabels': False,
             'fixedrange': True}
    yaxis = {'fixedrange': True}
    fig.update_layout(barmode='stack',
                      showlegend=False,
                      margin={'t': 0, 'b': 0, 'l': 0, 'r': 0},
                      xaxis=xaxis,
                      yaxis=yaxis,
                      plot_bgcolor='rgb(255, 255, 255)',
                      transition={
                          'duration': 500,
                          'easing': 'cubic-in-out'
                      }
    )
    return(fig)

def score_bar():
    fig = get_score_bar_figure(33, 34, 33)

    #the height of the component is set relative to it's width
    #this is achieved by the padding hack from
    #https://stackoverflow.com/questions/8894506/can-i-scale-a-divs-height-proportionally-to-its-width-using-css
    component = dcc.Graph(id='score-bar',
                          figure=fig,
                          style={'width': '100%', 'height': '100%',
                                 'position': 'absolute', 'left': 0},
                          config={'displayModeBar': False}
                          )
    container = html.Div(style={
        'position': 'relative',
        'width': '100%',
        'paddingBottom': RELATIVE_HEIGHT_OF_SCORE_BAR,
        'float': 'left',
        'height': 0})

    container.children = component
    return(container)

def fen_component():
    fen_pgn_container = html.Div(style={
        'position': 'relative',
        'width': '100%',
        'paddingBottom': FEN_PGN_COMPONENT_RELATIVE_HEIGHT,
        'float': 'left',
        'height': 0})

    fen_component = html.Div(id='fen-component', style=FEN_COMPONENT_STYLE)
    add_button = html.Button(id='add-fen',
                             children=['Add fen'],
                             style={'marginRight': '5px', 'marginBottom': '3px'})
    fen_input = dcc.Input(id='fen-input',
                          type='text',
                          #size="70",#"92", #"70"
                          autoComplete="off",
                          style={'font-size': '12px', 'width': '100%'}
                          #style={'flex': 1},
                          )

    click_mode = dcc.Checklist(id='click-mode',
                                      options=[{'label': 'Add also parents of clicked node',
                                                'value': 'add-also-parents'}],
                                      value=['add-also-parents'])

    add_startpos = html.Button(id='add-startpos',
                             children=['Add start position'],
                             style={'marginRight': '5px', 'marginBottom': '3px'}) #, 'marginTop': '5px'

    add_buttons = html.Div(children=[add_button, add_startpos],
                           style={'display': 'flex'})

    upload = dcc.Upload(
            id='upload-pgn',
            children=[html.Div(style={'flex':1}),
                      html.Div([
                          'Drag and Drop a pgn file or ',
                          html.A('Select File')
                      ],
                          style={'flex': 1}),
                      html.Div(style={'flex': 1})],
            style=PGN_COMPONENT_STYLE,
            # Only one pgn allowed
            multiple=False
        )

    fen_added_indicator = html.Div(id='fen-added', style={'display': 'none'})
    fen_deleted_indicator = html.Div(id='data-deleted-indicator', style={'display': 'none'})
    fen_component.children = [add_buttons, fen_input, click_mode, fen_added_indicator, fen_deleted_indicator]
    fen_pgn_container.children = [fen_component, upload]
    return(fen_pgn_container)

def position_pane():
    quit_btn = quit_button()

    mode_selector = html.Div(children=[dcc.RadioItems(id='position-mode-selector',
                                                      options=[{'label': 'pgn', 'value': 'pgn'},
                                                               {'label': 'fen', 'value': 'fen'},
                                                               ],
                                                      value='pgn')],
                             style={'marginBottom': '3px'})

    fen_input = fen_component()

    arrow_settings = html.Div(style={'display': 'flex',
                                     'flexDirection': 'row',
                                     'alignItems': 'center',
                                     'padding': '3px', 'paddingTop': '5px'})
    arrow_options = html.Div(children=[html.Label('Arrows: '),
        dcc.Dropdown(#RadioItems(
            id='arrow-type-selector',
            options=[
                {'label': 'Policy-%', 'value': 'p'},
                {'label': 'Visit-%', 'value': 'n'},
                {'label': 'Q-%', 'value': 'q'},
                {'label': 'Moves left (low)', 'value': 'ml_low'},
                {'label': 'Moves left (high)', 'value': 'ml_high'},

            ],
            #optionHeight=12,
            value='n',
            clearable=False,
            #labelStyle={'paddingLeft': '3px'},
            style={'flex': 1,
                   #'height': '2em',
                   #'display': 'inline-block',
                   'marginLeft': '3px',
                   }
    )],
                             style={'flex': 1, 'display': 'flex', 'flexDirection': 'row',
                                    'alignItems': 'center', 'marginRight': '6px'})
    arrows_input = html.Div(children=[html.Label('#: '),
                                      dcc.Input(id='nr_of_arrows_input', type="number",
                                                min=0, max=100, step=1,
                                                size='3', #size has effect in firefox
                                                inputMode='numeric', value=3)],
                            )

    arrow_settings.children = [arrow_options, arrows_input]

    img = html.Img(id='board')
    pgn_info = html.Div(id='pgn-info',
                         style={'height': '5em'})
    fen_text = html.Div(id='fen-text',
                         style={'height': '1.5em',
                                'font-size': '12px'})

    buttons = html.Div(children=[
        html.Button('Analyze all',
                    id='generate-data-button',
                    title='Load pgn to analyze',
                    style={'flex': '1', 'padding': '5px', 'marginRight': '5px',
                           'marginTop': '8px', 'marginBottom': '5px'}),
        html.Button('Analyze selected',
                    id='generate-data-selected-button',
                    title='',
                    style={'flex': '1', 'padding': '5px', 'marginLeft': '5px',
                           'marginTop': '8px', 'marginBottom': '5px'})],
    style={'display': 'flex', 'flexDirection': 'row'})

    data_table = dash_table.DataTable(
            id='move-table',
            columns=PGN_MODE_COLUMNS,
            fixed_rows={'headers': True, 'data': 0},
            style_cell={'textAlign': 'left', 'minWidth': '5px', 'width': '20px', 'maxWidth': '20px',
                        'whiteSpace': 'normal', 'height': 'auto', 'overflow': 'hidden'},
            # row_selectable='single',
            style_as_list_view=True,
            style_table={'width': '100%', 'marginLeft': '0px', 'overflowY': 'auto',
                         #'borderLeft': f'1px solid {BAR_LINE_COLOR}', 'borderTop': f'1px solid {BAR_LINE_COLOR}',
                         #'boxSizing': 'border-box', 'display:': 'inline-block'
                         },  # , 'maxHeight': '300px', 'overflowY': 'scroll'},#'height': '750px'
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }],
            style_cell_conditional=[
                {
                    'if': {'column_id': 'Q'},
                    'textAlign': 'right'
                },
                {
                    'if': {'column_id': 'W'},
                    'textAlign': 'right'
                },
                {
                    'if': {'column_id': 'D'},
                    'textAlign': 'right'
                },
                {
                    'if': {'column_id': 'L'},
                    'textAlign': 'right'
                },
                {
                    'if': {'column_id': 'M'},
                    'textAlign': 'right'
                }
            ],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            css=[{"selector": "table", "rule": "width: 100%;"},{"selector": ".dash-spreadsheet.dash-freeze-top, .dash-spreadsheet .dash-virtualized", "rule": "max-height: none;"}],

        )
    container_table = html.Div(html.Div(children=data_table, style={'borderLeft': f'1px solid {BAR_LINE_COLOR}', 'borderTop': f'1px solid {BAR_LINE_COLOR}'}),
    style={'flex': '1', 'overflow': 'auto', })
    container = html.Div(style={'height': '100%', 'width': COMPONENT_WIDTH, 'display': 'flex', 'flexDirection': 'column'})
    content = [quit_btn, mode_selector, fen_input, arrow_settings, img, score_bar(), fen_text, pgn_info, buttons, container_table]
    container.children = content
    return(container)

def parse_pgn(contents, filename, is_new_pgn):
    if contents is None:
        return(dash.no_update)
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'pgn' in filename:
            # Assume that the user uploaded a pgn file
            first_game = chess.pgn.read_game(io.StringIO(decoded.decode('utf-8')))
        else:
            return('Not a pgn')
    except Exception as e:
        return('Upload failed')

    if is_new_pgn:
        board = first_game.board()
        fen = board.fen()
        game_data_pgn.board = board
        data = [{'dummy_left': '', 'ply': 0, 'move': '-', 'turn': board.turn, 'fen': fen, 'dummy_right': ''}]

        for ply, move in enumerate(first_game.mainline_moves()):
            row = {}
            san = board.san(move)

            row['move'] = san
            row['ply'] = ply + 1
            row['turn'] = not board.turn
            board.push(move)
            row['fen'] = board.fen()
            row['dummy_left'] = ''
            row['dummy_right'] = ''

            data.append(row)

        game_data_pgn.data = data
        game_data_pgn.fen = fen
        # reset analysis of previous pgn
        tree_data_pgn.reset_data()

    game_info = f'**File**: {filename}\n'
    game_info += f'**White**: {first_game.headers.get("White", "?")}\n'
    game_info += f'**Black**: {first_game.headers.get("Black", "?")}'
    game_info = dcc.Markdown(game_info, style={"whiteSpace": "pre"})
    return(game_info)


@app.callback(
    Output('move-table', 'style_data_conditional'),
    [Input('move-table', 'active_cell'),])
def row_highlight(active_cell):
    style_data_conditional=[
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(248, 248, 248)'
        }
    ]

    if active_cell is None:
        return style_data_conditional

    ind = active_cell['row']
    highligh = {
            'if': {'row_index': ind},
            'backgroundColor': SELECTED_ROW_COLOR
        }
    style_data_conditional.append(highligh)
    return(style_data_conditional)


X = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
Y = ['1', '2', '3', '4', '5', '6', '7', '8']
move_table = {x+y: 8*Y.index(y)+X.index(x) for y in Y for x in X}

def get_arrows(position_id, slider_value, type, nr_of_arrows, position_mode):
    if position_mode == 'pgn':
        tree_data = tree_data_pgn
    else:
        tree_data = tree_data_fen

    if nr_of_arrows == 0 or nr_of_arrows is None:
        return([])
    moves, metrics = tree_data.get_best_moves(position_id=position_id,
                                              slider_value=slider_value,
                                              type=type,
                                              max_moves=nr_of_arrows)

    r,g,b = ARROW_COLORS[type]#POLICY_ARROW_COLOR#[23,178,207]#[0, 255, 0]
    if metrics == []:
        return([])
    arrows = []
    best_metric = metrics[0]
    for move, metric in zip(moves, metrics):
        from_square = move[:2]
        to_square = move[2:4]
        tail = move_table[from_square]
        head = move_table[to_square]
        #the worse the move is, the more desaturated the arrow color shall be

        if type == 'q':
            saturation_factor = ((1+metric)/(1+best_metric))**1.618
        elif type == 'ml_low' or type == 'ml_high':
            #saturation_factor = ((1+best_metric)/(1+metric))**1.618
            worst_metric = metrics[-1]
            if worst_metric == best_metric:
                saturation_factor = 1.0
            else:
                saturation_factor = (metric - worst_metric)/(best_metric - worst_metric)
        else:
            saturation_factor = (metric / best_metric) ** 0.618
        r,g,b = rgb_adjust_saturation(saturation_factor, r, g, b)
        color = f"rgb({r}, {g}, {b})"#"rgb(0, 255, 0)"#"#FF0000"
        if type not in ('ml_low, ml_high'):
            annotation = f'{round(100*metric)}'
        else:
            annotation = f'{round(metric)}'
        arrow = svg.Arrow(tail, head, color=color, annotation=annotation)
        arrows.append(arrow)
    return(arrows)


def svg_board_image(board, arrows, last_move):
    svg_str = str(svg.board(board, size=200, arrows=arrows, lastmove=last_move, coordinates=SHOW_BOARD_COORDINATES))
    svg_str = svg_str.replace('height="200"', 'height="100%"')
    svg_str = svg_str.replace('width="200"', 'width="100%"')
    svg_byte = svg_str.encode()
    encoded = base64.b64encode(svg_byte)
    svg_board = 'data:image/svg+xml;base64,{}'.format(encoded.decode())
    return(svg_board)

@app.callback(
    Output('board', 'src'),
    [Input('move-table', 'active_cell'),
     Input('slider1', 'value'),
     Input('arrow-type-selector', 'value'),
     Input('nr_of_arrows_input', 'value'),
     Input('position-mode-selector', 'value')])
def update_board_image(active_cell, slider_value, arrow_type, nr_of_arrows, position_mode):
    triggerers = dash.callback_context.triggered
    triggered_by_position_mode = False
    for triggerer in triggerers:
        if triggerer['prop_id'] == 'position-mode-selector.value':
            triggered_by_position_mode = True
            break

    if position_mode == 'pgn':
        game_data = game_data_pgn
    else:
        game_data = game_data_fen

    game_data.board.set_fen(game_data.pgn_start_fen)
    board = game_data.board
    if active_cell is None:
        board.reset()
        return(svg_board_image(board, [], None))
    elif triggered_by_position_mode:
        selected_row_id = 0
    else:
        selected_row_id = active_cell['row']

    last_move = None
    position_id = game_data.get_position_id(selected_row_id)
    if position_mode == 'pgn':
        for i in range(1, selected_row_id + 1):
            move = game_data.get_value_by_row_id('move', i) #game_data.data['move'][i]
            last_move = board.push_san(move)
    else:
        game_data.set_board_position(position_id)
        board = game_data.board #probably not needed to set again
    arrows = get_arrows(position_id, slider_value, arrow_type, nr_of_arrows, position_mode)
    #reverse the order so that better moves are drawn above worse moves
    arrows = arrows[::-1]
    svg_board = svg_board_image(board, arrows, last_move)
    #svg_str = str(svg.board(board, size=200, arrows=arrows, lastmove=last_move, coordinates=SHOW_BOARD_COORDINATES))
    #svg_str = svg_str.replace('height="200"', 'height="100%"')
    #svg_str = svg_str.replace('width="200"', 'width="100%"')
    #svg_byte = svg_str.encode()
    #encoded = base64.b64encode(svg_byte)
    #svg_board = 'data:image/svg+xml;base64,{}'.format(encoded.decode())
    return(svg_board)

@app.callback(
     Output('pgn-info', 'children'),
    [Input('upload-pgn', 'contents'),
     Input('position-mode-selector', 'value')],
    [State('upload-pgn', 'filename')]
)
def update_pgn(content, position_mode, filename):
    triggerers = dash.callback_context.triggered
    is_new_pgn = True
    for triggerer in triggerers:
        if triggerer['prop_id'] == 'position-mode-selector.value':
            is_new_pgn = False
            break
    if position_mode == 'fen':
        return('')
    return(parse_pgn(content, filename, is_new_pgn))

@app.callback(
     Output('fen-text', 'children'),
    [Input('move-table', 'active_cell')],
    [State('position-mode-selector', 'value')]
)
def update_fen_text(active_cell, position_mode):
    if active_cell is None:
        return('')
    if position_mode == 'fen':
        game_data = game_data_fen
    else:
        game_data = game_data_pgn
    if game_data.data is not None:
        row = active_cell['row']
        fen = game_data.get_value_by_row_id('fen', row)
        return(fen)
    return('')


@app.callback(
    Output('move-table', 'data'),
    [Input('pgn-info', 'children'),
     Input('hidden-div-slider-state', 'children'),
     Input('position-mode-selector', 'value'),
     Input('fen-added', 'children')],
)
def update_datatable(text, slider_state, position_mode, fen_added):
    if position_mode == 'pgn':
        game_data = game_data_pgn
    else:
        game_data = game_data_fen
    data = game_data.data
    if (text is None and fen_added is None) or data is None:
        return([])
    return(data)

@app.callback([
     Output('move-table', 'active_cell'),
     Output('move-table', 'selected_cells')],
    [Input('upload-pgn', 'contents'),
     Input('generate-data-button', 'title'),
     Input('fen-added', 'children'),
     Input('position-mode-selector', 'value'),
     #Input('data-deleted-indicator', 'children'),
     ],
    [State('move-table', 'active_cell')])
def reset_selected_cells(arg1, arg2, fen_added, position_mode, active_cell): # data_deleted
    triggerers = dash.callback_context.triggered
    triggered_by_fen = False
    triggered_by_position_mode = False
    triggered_by_delete = False
    for triggerer in triggerers:
        if triggerer['prop_id'] == 'fen-added.children':
            triggered_by_fen = True
            break
        elif triggerer['prop_id'] == 'position-mode-selector.value':
            triggered_by_position_mode = True
            break
        elif triggerer['prop_id'] == 'data-deleted-indicator.children':
            triggered_by_delete = True
    if triggered_by_fen:
        row_of_new_fen = len(game_data_fen.data) - 1
        active_cell = {'row': row_of_new_fen, 'column': 0}
    elif active_cell is None or triggered_by_position_mode or triggered_by_delete:
        active_cell = {'row': 0, 'column': 0}
    selected_cells = [active_cell]
    return(active_cell, selected_cells)

@app.callback([
     Output('generate-data-selected-button', 'disabled'),
     Output('generate-data-selected-button', 'title')],
    [Input('move-table', 'active_cell')])
def set_state_of_analyze_selected_button(active_cell):
    if active_cell is None:
        disabled = True
        title = 'First, select a position to analyze'
    else:
        disabled = False
        title = 'Analyze selected position'
    return(disabled, title)

@app.callback(
    [Output('score-bar', 'figure'),
     Output('score-bar', 'style')],
    [Input('hidden-div-slider-state', 'children'),
     Input('move-table', 'active_cell')],
    [State('position-mode-selector', 'value'),
     ])
def update_score_bar(value, active_cell, position_mode):
    if position_mode == 'pgn':
        tree_data = tree_data_pgn
        game_data = game_data_pgn
    else:
        tree_data = tree_data_fen
        game_data = game_data_fen
    style = {'width': '100%', 'height': '100%', 'position': 'absolute', 'left': 0, 'visibility': 'visible'}

    if active_cell is None or game_data.data is None or game_data.get_position_id(active_cell['row']) not in tree_data.data:
        style['visibility'] = 'hidden'
        return(dash.no_update, style)

    row = active_cell['row']
    W = game_data.data[row]['W']
    D = game_data.data[row]['D']
    B = game_data.data[row]['L']
    if W is None:
        style['visibility'] = 'hidden'
        return(dash.no_update, style)

    fig = get_score_bar_figure(W, D, B)
    return(fig, style)

@app.callback([
     Output('fen-component', 'style'),
     Output('upload-pgn', 'style'),
     Output('move-table', 'columns'),
     Output('move-table', 'row_deletable')],
    [Input('position-mode-selector', 'value')])
def set_position_upload_mode(mode):
    fen_style = copy.copy(FEN_COMPONENT_STYLE)
    pgn_style = copy.copy(PGN_COMPONENT_STYLE)
    if mode == 'fen':
        columns = FEN_MODE_COLUMNS
        pgn_style['display'] = 'none'
        row_deletable = True
    elif mode =='pgn':
        columns = PGN_MODE_COLUMNS
        fen_style['display'] = 'none'
        row_deletable = False
    else:
        fen_style = dash.no_update
        pgn_style = dash.no_update
        columns = dash.no_update
        row_deletable = dash.no_update
    return(fen_style, pgn_style, columns, row_deletable)

@app.callback([Output('fen-input', "value"),
               Output('fen-input', 'placeholder'),
               Output('fen-added', 'children')],
    [Input('add-fen', 'n_clicks'),
     Input('add-startpos', 'n_clicks'),
     Input('graph', 'clickData')],
    [State('fen-input', 'value'),
     State('position-mode-selector', 'value'),
     State('move-table', 'active_cell'),
     State('slider1', 'value'),
     State('click-mode', 'value')
     ])
def add_fen(n_clicks_fen, n_clicks_startpos, click_data, fen, position_mode, active_cell, slider_value, click_mode):

    if position_mode != 'fen' or (n_clicks_fen is None and n_clicks_startpos is None):
        return(dash.no_update, dash.no_update, dash.no_update)

    triggerers = dash.callback_context.triggered
    add_fen = False
    add_startpos = False
    add_from_node = False
    for triggerer in triggerers:
        if triggerer['prop_id'] == 'add-fen.n_clicks':
            add_fen = True
        elif triggerer['prop_id'] == 'add-startpos.n_clicks':
            add_startpos = True

        elif triggerer['prop_id'] == 'graph.clickData':
            add_from_node = True

    fens = []
    if add_from_node:
        tree_data = tree_data_fen
        game_data = game_data_fen
        row = active_cell['row']
        position_id = game_data.get_position_id(row)
        node_id = click_data['points'][0]['customdata']
        moves = pt.get_moves(tree_data.G_dict[position_id][slider_value], node_id)
        board = chess.Board()
        start_fen = game_data.get_value_by_position_id('fen', position_id)
        if click_mode == ['add-also-parents']: #add also positions of intermediate nodes between clicked and root node
            for i in range(len(moves)):
                board = pt.set_board(moves[:i+1], board, start_fen)
                fens.append(board.fen())
        else:
            board = pt.set_board(moves, board, start_fen)
            fen = board.fen()

    elif add_startpos:
        if n_clicks_startpos is None:
            return (dash.no_update, dash.no_update, dash.no_update)
        fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

    if add_fen and (fen is None or n_clicks_fen is None):
        return (dash.no_update, dash.no_update, dash.no_update)

    if fens == []:
        try:
            game_data_fen.board.set_fen(fen)
        except ValueError:
            return('', 'not a valid fen', dash.no_update)

    if fens != []:
        for fen in fens:
            fen_id = game_data_fen.add_fen(fen)
    else:
        fen_id = game_data_fen.add_fen(fen)
    return (dash.no_update, '', fen_id)


@app.callback(Output('data-deleted-indicator', 'children'),
              [Input('move-table', 'data')],
              [State('position-mode-selector', 'value')])
def data_row_delete(data, position_mode):
    if position_mode != 'fen':
        return(dash.no_update)
    previous_data = game_data_fen.data_previous
    if data is None or previous_data is None:
        return(dash.no_update)
    deleted_row = None


    position_ids_in_table = [d['ply'] for d in data]
    position_ids_in_previous_table = [d['ply'] for d in previous_data]
    for row_index, position_id in enumerate(position_ids_in_previous_table):
        if position_id not in position_ids_in_table:
            deleted_row = row_index
            deleted_position_id = position_id
            break

    if data == []:
        game_data_fen.data = None
        game_data_fen.data_previous = None
        tree_data_fen.data = {}
        tree_data_fen.G_dict = {}
        tree_data_fen.heatmap_data_for_moves = {}
        tree_data_fen.heatmap_data_for_board_states = {}
        return(deleted_row)

    if deleted_row is None:
        return (dash.no_update)
    tree_data_fen.data.pop(deleted_position_id, None) #try to delete corresponding tree data
    tree_data_fen.G_dict.pop(deleted_position_id, None)
    tree_data_fen.heatmap_data_for_moves.pop(deleted_position_id, None)
    tree_data_fen.heatmap_data_for_board_states.pop(deleted_position_id, None)
    game_data_fen.data.pop(deleted_row)
    game_data_fen.data_previous = game_data_fen.data
    return(deleted_row)


