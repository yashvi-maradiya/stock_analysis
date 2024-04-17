import dash
from dash import html, dcc, Input, Output, State
from yfinance_data import Yfinance
from ta_lib_utility import calculate_rsi, calculate_macd, calculate_dmi_and_adx, calculate_roc,calculate_moving_averages, calculate_bollinger_bands_width,handle_candle_pattern
from plotly.subplots import make_subplots

import plotly.graph_objs as go
import pandas as pd
from candles import candle_patterns
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Stock Analysis Application",style={'textalign': 'center'}),
    html.Div([
        html.Label("Company Name :", style={'margin-right' : '10px'}),
        dcc.Input(id='my-input', type='text', placeholder='Enter company name', style={'margin-right': '10px'}),
        html.Label("Time range:", style={'margin-right': '10px'}),
        dcc.Dropdown(
            id='time-range-dropdown',
            options=[
                {'label': '1D', 'value': '1d'},
                {'label': '5D', 'value': '5d'},
                {'label': '1M', 'value': '1mo'},
                {'label': '3M', 'value': '3mo'},
                {'label': '6M', 'value': '6mo'},
                {'label': 'YTD', 'value': 'ytd'},
                {'label': '1Y', 'value': '1y'},
                {'label': '2Y', 'value': '2y'},
                {'label': '5Y', 'value': '5y'},
                {'label': 'MAX', 'value': 'max'}
            ],
            value='1mo',
            style={'width': '100px', 'margin-right': '10px'}
        ),
        html.Label("Interval time:", style={'margin-right': '10px'}),
        dcc.Dropdown(
            id='interval_time',
            options=[
                {'label': 'Hourly', 'value': '1h'},
                {'label': 'Daily', 'value': '1d'},
                {'label': 'Weekly', 'value': '1wk'},
            ],
            value='1d',
            style={'margin-right': '10px', 'width': '100px', 'margin-left': '5px'}
        ),
        html.Button('Submit', id='submit-button', n_clicks=0),
    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px'}),

    html.Div([
        dcc.Graph(
            id='candlestick-chart',
            style={'width': '1200px'}
        )
    ]),

    html.Div(id='volume-chart'),
    html.Div(id='rsi-chart'),
    html.Div(id='macd-chart'),
    html.Div(id='dmi-adx-chart'),
    html.Div(id='roc-chart'),
    html.Div(id='bollinger_bands_width')
], style={'background-color': '#add8e6', 'padding': '20px', 'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'})

def get_range_breaks(data):
    date_series = pd.Series(data.index)
    gaps = date_series[date_series.diff() > pd.Timedelta(days=1)]

    rangebreaks = []

    for idx in gaps.index:
        rangebreaks.append(
            {
                "bounds": [
                    date_series.iloc[idx - 1] + pd.Timedelta(days=1),
                    date_series.iloc[idx]
                ]
            }
        )

    return rangebreaks

def sub_plot(data, stock_name, rangebreaks):
    volume_trace = go.Bar(
        x=data.index,
        y=data['Volume'],
        name='Volume',
        marker=dict(color='cyan')
    )

    layout = {
        'xaxis': {'title': 'Date', 'rangebreaks': rangebreaks, 'rangeslider': {'visible': False}},
        'yaxis': {'title': 'Volume'},
        'plot_bgcolor': 'black',
        'paper_bgcolor': 'black',
        'font': {'color': '#FFFFFF'},
        'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50},
        'height': 200,
        'width': 1200,
        'legend': {'orientation': 'h', 'y': 1.1},
        'hovermode': 'x unified',
        'hoverlabel': {'bgcolor': '#FFFFFF', 'font': {'color': '#333333'}},
        'template': 'plotly_dark'
    }

    fig = go.Figure(data=[volume_trace], layout=layout)

    return html.Div(
        dcc.Graph(id='volume-plot', figure=fig)
    )

@app.callback(
    Output('candlestick-chart', 'figure'),
    Output('volume-chart', 'children'),
    Output('rsi-chart', 'children'),
    Output('macd-chart', 'children'),
    Output('dmi-adx-chart', 'children'),
    Output('roc-chart','children'),
    Output('bollinger_bands_width','children'),
    [Input('submit-button', 'n_clicks')],
    [State('my-input', 'value'),
     State('time-range-dropdown', 'value'),
     State('interval_time', 'value')]
)
def update_output(n_clicks, input_value, time_range_value, interval_time):
    if n_clicks:
        try:
            yf_obj = Yfinance(input_value)
            stock_data = yf_obj.fetch_stock_data(time_range_value, interval_time)


            
            trading_ticker = input_value.split('.')[0]
            title_html = f'<a href="https://www.tradingview.com/symbols/{trading_ticker}" target="_blank">{input_value}</a>'

            stock_info = yf_obj.get_stock_info()

            market_cap = stock_info['marketCap']
            market_cap_suffixes = {
                6: 'million',
                9: 'billion',
                12: 'trillion'
            }

            magnitude = len(str(market_cap)) - 1
            if magnitude >= 6:
                market_cap_str = f"{market_cap / 10 ** (magnitude):,.2f} {market_cap_suffixes.get(magnitude, '')}"
            else:
                market_cap_str = f"{market_cap:,}"

            exchange = stock_info.get('exchange')
            stock_currency = stock_info.get('financialCurrency')

            company_info = f"Company: {stock_info['shortName']}<br>Market Cap: {market_cap_str} {stock_currency}<br>Next Earnings Date: {', '.join(yf_obj.get_stock_earning_date())}<br>Sector: {stock_info['sector']}"
            candlestick = go.Candlestick(
                x=stock_data.index,
                open=stock_data['Open'],
                high=stock_data['High'],
                low=stock_data['Low'],
                close=stock_data['Close']
            )
            
            # Define layout
            layout = go.Layout(
                title=title_html,
                xaxis_title='Date',
                yaxis_title='Price',
                plot_bgcolor='black',
                paper_bgcolor='black',
                xaxis=dict(title='Date', rangebreaks=get_range_breaks(stock_data), showgrid=False,
                           zeroline=False, tickfont=dict(color='white'), rangeslider=dict(visible=False)),
                yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='white')),
                font=dict(color='white'),
                annotations=[
                    {
                        'x': 0.10,
                        'y': 1.05,
                        'xref': 'paper',
                        'yref': 'paper',
                        'xanchor': 'left',
                        'yanchor': 'bottom',
                        'text': company_info,
                        'showarrow': False,
                        'font': {'color': 'white'},
                        'align': 'left'
                    }
                ],
                
            )

            # Calculate moving averages
            stock_data = calculate_moving_averages(stock_data)
            # Handle candlestick patterns
            stock_data = handle_candle_pattern(stock_data)

            # Define moving average traces
            short_ma_trace = go.Scatter(
                x=stock_data.index,
                y=stock_data['Short MA'],
                mode='lines',
                name='Short MA',
                line=dict(color='orange')
            )

            medium_ma_trace = go.Scatter(
                x=stock_data.index,
                y=stock_data['Medium MA'],
                mode='lines',
                name='Medium MA',
                line=dict(color='blue')
            )

            long_ma_trace = go.Scatter(
                x=stock_data.index,
                y=stock_data['Long MA'],
                mode='lines',
                name='Long MA',
                line=dict(color='red')
            )

            # Define colors for candlestick patterns
            pattern_colors = ['Orange', 'Cyan', 'Fuchsia', 'Red', 'SpringGreen', 'Yellow', 'Chartreuse', 'Magenta']
            start_index = 3

            pattern_traces = []
            color_index = 0

            # Loop through columns to find candlestick patterns
            for pattern in stock_data.columns:
                if pattern.endswith('_result'):
                    pattern_name = pattern[start_index:].replace('_result', '').replace('_', ' ').title()
                    color = pattern_colors[color_index % len(pattern_colors)]
                    pattern_key = pattern[:-len('_result')]
                    pattern_description = candle_patterns[pattern_key]['description']

                    pattern_trace = go.Scatter(
                        x=stock_data.index,
                        y=stock_data[pattern],
                        mode='markers',
                        name=pattern_name,
                        marker=dict(
                            color=color,
                            size=10,
                        ),
                        opacity=0.8,
                        text=pattern_description,
                    )

                    pattern_traces.append(pattern_trace)
                    color_index += 1

            # Create subplots
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05)

            # Add traces to subplots
            fig.add_trace(candlestick, row=1, col=1)
            fig.add_trace(short_ma_trace, row=1, col=1)
            fig.add_trace(medium_ma_trace, row=1, col=1)
            fig.add_trace(long_ma_trace, row=1, col=1)

            for pattern_trace in pattern_traces:
                fig.add_trace(pattern_trace, row=2, col=1)

            # Update layout
            fig.update_layout(layout)

            volume_sub_plot = sub_plot(stock_data, input_value, get_range_breaks(stock_data))
            stock_data = yf_obj.fetch_stock_data('1y', interval_time)

            rsi_data = calculate_rsi(stock_data)
            rsi_trace = go.Scatter(x=rsi_data.index, y=rsi_data['RSI'], name='RSI', line=dict(color='orange'))

            rsi_layout = {
                'xaxis': {'title': 'Date', 'rangebreaks': get_range_breaks(rsi_data), 'showgrid': False, 'zeroline': False,
                          'tickfont': {'color': 'white'}, 'rangeslider': {'visible': False}},
                'yaxis': {'title': 'RSI', 'showgrid': False, 'zeroline': False, 'tickfont': {'color': 'white'}},
                'plot_bgcolor': 'black',
                'paper_bgcolor': 'black',
                'font': {'color': '#FFFFFF'},
                'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50},
                'height': 200,
                'width': 1200,
                'legend': {'orientation': 'h', 'y': 1.1},
                'hovermode': 'x unified',
                'hoverlabel': {'bgcolor': '#FFFFFF', 'font': {'color': '#333333'}},
                'template': 'plotly_dark'
            }

            rsi_fig = go.Figure(data=[rsi_trace], layout=rsi_layout)

            macd_data = calculate_macd(stock_data)
            macd_trace = go.Scatter(x=macd_data.index, y=macd_data['MACD'], name='MACD', line=dict(color='blue'))
            signal_trace = go.Scatter(x=macd_data.index, y=macd_data['MACD_Signal'], name='Signal', line=dict(color='red'))

            macd_layout = {
                'xaxis': {'title': 'Date', 'rangebreaks': get_range_breaks(macd_data), 'showgrid': False, 'zeroline': False,
                          'tickfont': {'color': 'white'}, 'rangeslider': {'visible': False}},
                'yaxis': {'title': 'MACD', 'showgrid': False, 'zeroline': False, 'tickfont': {'color': 'white'}},
                'plot_bgcolor': 'black',
                'paper_bgcolor': 'black',
                'font': {'color': '#FFFFFF'},
                'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50},
                'height': 200,
                'width': 1200,
                'legend': {'orientation': 'h', 'y': 1.1},
                'hovermode': 'x unified',
                'hoverlabel': {'bgcolor': '#FFFFFF', 'font': {'color': '#333333'}},
                'template': 'plotly_dark'
            }

            macd_fig = go.Figure(data=[macd_trace, signal_trace], layout=macd_layout)

            dmi_adx_data = calculate_dmi_and_adx(stock_data)
            dmi_trace = go.Scatter(x=dmi_adx_data.index, y=dmi_adx_data['DMI+'], name='DMI+', line=dict(color='green'))
            adx_trace = go.Scatter(x=dmi_adx_data.index, y=dmi_adx_data['ADX'], name='ADX', line=dict(color='purple'))

            dmi_adx_layout = {
                'xaxis': {'title': 'Date', 'rangebreaks': get_range_breaks(dmi_adx_data), 'showgrid': False, 'zeroline': False,
                          'tickfont': {'color': 'white'}, 'rangeslider': {'visible': False}},
                'yaxis': {'title': 'DMI/ADX', 'showgrid': False, 'zeroline': False, 'tickfont': {'color': 'white'}},
                'plot_bgcolor': 'black',
                'paper_bgcolor': 'black',
                'font': {'color': '#FFFFFF'},
                'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50},
                'height': 200,
                'width': 1200,
                'legend': {'orientation': 'h', 'y': 1.1},
                'hovermode': 'x unified',
                'hoverlabel': {'bgcolor': '#FFFFFF', 'font': {'color': '#333333'}},
                'template': 'plotly_dark'
            }

            dmi_adx_fig = go.Figure(data=[dmi_trace, adx_trace], layout=dmi_adx_layout)

            roc_data = calculate_roc(stock_data)
            roc_trace = go.Scatter(x=roc_data.index, y=roc_data['ROC'], name='ROC', line=dict(color='green'))
            roc_layout = {
                'xaxis': {'title': 'Date', 'rangebreaks': get_range_breaks(roc_data), 'showgrid': False, 'zeroline': False,
                          'tickfont': {'color': 'white'}, 'rangeslider': {'visible': False}},
                'yaxis': {'title': 'ROC', 'showgrid': False, 'zeroline': False, 'tickfont': {'color': 'white'}},
                'plot_bgcolor': 'black',
                'paper_bgcolor': 'black',
                'font': {'color': '#FFFFFF'},
                'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50},
                'height': 200,
                'width': 1200,
                'legend': {'orientation': 'h', 'y': 1.1},
                'hovermode': 'x unified',
                'hoverlabel': {'bgcolor': '#FFFFFF', 'font': {'color': '#333333'}},
                'template': 'plotly_dark'
            }

            roc_fig = go.Figure(data=[roc_trace], layout=roc_layout)

            bollinger_data = calculate_bollinger_bands_width(stock_data)
            bollinger_trace = go.Scatter(x=bollinger_data.index, y=bollinger_data['BB_Width'], name='Bollinger_bands', line=dict(color='orange'))
            bollinger_layout = {
                'xaxis': {'title': 'Date', 'rangebreaks': get_range_breaks(bollinger_data), 'showgrid': False, 'zeroline': False,
                          'tickfont': {'color': 'white'}, 'rangeslider': {'visible': False}},
                'yaxis': {'title': 'Bollinger Bands', 'showgrid': False, 'zeroline': False, 'tickfont': {'color': 'white'}},
                'plot_bgcolor': 'black',
                'paper_bgcolor': 'black',
                'font': {'color': '#FFFFFF'},
                'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50},
                'height': 200,
                'width': 1200,
                'legend': {'orientation': 'h', 'y': 1.1},
                'hovermode': 'x unified',
                'hoverlabel': {'bgcolor': '#FFFFFF', 'font': {'color': '#333333'}},
                'template': 'plotly_dark'
            }

            bollinger_fig = go.Figure(data=[bollinger_trace], layout=bollinger_layout)


            return fig, volume_sub_plot, dcc.Graph(id='rsi-plot', figure=rsi_fig), dcc.Graph(id='macd-plot', figure=macd_fig), dcc.Graph(id='dmi-adx-plot', figure=dmi_adx_fig),dcc.Graph(id='roc-plot', figure=roc_fig),dcc.Graph(id='bollinger-plot', figure=bollinger_fig)

        except Exception as e:
            error_message = str(e) if e else "Unknown error"
            return (
                {'data': [], 'layout': {'title': 'Error', 'annotations': [{'text': f'Error fetching data: {error_message}', 'x': 0.5, 'y': 0.5, 'showarrow': False}], 'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'plot_bgcolor': 'black', 'paper_bgcolor': 'black'}},
                html.Div(),  # for volume-chart.children
                html.Div(),  # for rsi-chart.children
                html.Div(),  # for macd-chart.children
                html.Div(),  # for dmi-adx-chart.children
                html.Div(),  # for roc-chart.children
                html.Div()   # for bollinger_bands_width.children
            )

    return (
        {'data': [], 'layout': {'title': 'Error', 'annotations': [{'text': 'Error: No data fetched', 'x': 0.5, 'y': 0.5, 'showarrow': False}], 'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'plot_bgcolor': 'black', 'paper_bgcolor': 'black'}},
        html.Div(),  # for volume-chart.children
        html.Div(),  # for rsi-chart.children
        html.Div(),  # for macd-chart.children
        html.Div(),  # for dmi-adx-chart.children
        html.Div(),  # for roc-chart.children
        html.Div()   # for bollinger_bands_width.children
    )

if __name__ == '__main__':
    app.run_server(debug=True)