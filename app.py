import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import yfinance as yf
import requests

# ---------------------------
# Constants
# ---------------------------
CURRENCY_PAIRS = [
    ("EURUSD", "EUR/USD"),
    ("USDJPY", "USD/JPY"),
    ("GBPUSD", "GBP/USD"),
    ("USDCHF", "USD/CHF"),
    ("AUDUSD", "AUD/USD"),
    ("USDCAD", "USD/CAD"),
    ("NZDUSD", "NZD/USD"),
    ("EURJPY", "EUR/JPY"),
    ("EURGBP", "EUR/GBP"),
    ("USDSEK", "USD/SEK")
]

NEWSAPI_KEY = "cb38afd341454880aa2c24511fb37d4c"
NEWS_DOMAINS = "economist.com,ft.com,wsj.com,bloomberg.com,reuters.com"

# ---------------------------
# App Init
# ---------------------------
app = dash.Dash(__name__)
app.title = "GeoRisk Alpha Pro"

# ---------------------------
# Layout
# ---------------------------
app.layout = html.Div([
    html.Div([
        html.H1("🌍 GeoRisk Alpha Pro", style={"textAlign": "center"}),

        html.Div([
            html.Label("Enter up to 3 ISINs or Tickers (comma-separated):"),
            dcc.Input(id='asset-input', value='AAPL,GLD,EEM', type='text', style={"width": "100%"}),

            html.Label("Geopolitical Keyword:"),
            dcc.Input(id='keyword-input', value='war', type='text', style={"width": "100%"}),

            html.Label("Date Range:"),
            dcc.Dropdown(
                id='date-range',
                options=[
                    {"label": "1 Week", "value": "7d"},
                    {"label": "1 Month", "value": "1mo"},
                    {"label": "YTD", "value": "ytd"},
                    {"label": "Max", "value": "max"}
                ],
                value='1mo'
            ),

            html.Button("Run Analysis", id='run-btn', n_clicks=0)
        ], style={"padding": "20px"})
    ], style={"width": "25%", "display": "inline-block", "verticalAlign": "top"}),

    html.Div([
        dcc.Tabs(id='tabs', value='tab1', children=[
            dcc.Tab(label='📈 Asset Comparison', value='tab1'),
            dcc.Tab(label='🌍 FX Rates', value='tab2'),
            dcc.Tab(label='📰 Geopolitical News', value='tab3')
        ]),
        html.Div(id='tab-output')
    ], style={"width": "70%", "display": "inline-block", "padding": "20px"})
])

# ---------------------------
# Callbacks
# ---------------------------
@app.callback(
    Output('tab-output', 'children'),
    Input('run-btn', 'n_clicks'),
    State('asset-input', 'value'),
    State('keyword-input', 'value'),
    State('date-range', 'value'),
    State('tabs', 'value')
)
def update_tabs(n_clicks, assets, keyword, date_range, tab):
    if not assets:
        return html.Div("Please enter at least one asset.")

    asset_list = [x.strip().upper() for x in assets.split(',') if x.strip()]
    asset_data = {asset: yf.download(asset, period=date_range) for asset in asset_list}

    if tab == 'tab1':
        graphs = []
        for asset, df in asset_data.items():
            if not df.empty:
                graphs.append(go.Scatter(x=df.index, y=df['Close'], mode='lines', name=asset))
        layout = go.Layout(title="Asset Comparison", xaxis={"title": "Date"}, yaxis={"title": "Price"})
        return dcc.Graph(figure={"data": graphs, "layout": layout})

    elif tab == 'tab2':
        fx_data = {code: yf.download(code + "=X", period="7d") for code, _ in CURRENCY_PAIRS}
        rows = []
        for (code, name), df in zip(CURRENCY_PAIRS, fx_data.values()):
            if not df.empty:
                change = round((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100, 2)
                rows.append(html.Tr([html.Td(name), html.Td(f"{change}%")]))
        return html.Table([
            html.Thead(html.Tr([html.Th("Currency Pair"), html.Th("% Change (7d)")])),
            html.Tbody(rows)
        ])

    elif tab == 'tab3':
        url = f"https://newsapi.org/v2/everything?q={keyword}&language=en&sortBy=publishedAt&pageSize=5&domains={NEWS_DOMAINS}&apiKey={NEWSAPI_KEY}"
        r = requests.get(url).json()
        articles = r.get("articles", [])
        if not articles:
            return html.Div("No articles found.")

        cards = []
        for article in articles:
            cards.append(html.Div([
                html.H4(article['title']),
                html.P(article['description']),
                html.A("Read more", href=article['url'], target="_blank")
            ], style={"marginBottom": "20px", "padding": "10px", "border": "1px solid #ccc", "borderRadius": "5px"}))

        return html.Div(cards)

# ---------------------------
# Run App
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
