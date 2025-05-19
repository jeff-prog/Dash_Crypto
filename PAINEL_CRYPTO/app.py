import requests
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import datetime
import base64
from io import BytesIO
import matplotlib.pyplot as plt

app = dash.Dash(__name__)
app.title = "Painel Cripto em Tempo Real"

# Função para buscar os dados principais das criptos
def obter_criptos(moeda='usd', pagina=1):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": moeda,
        "order": "market_cap_desc",
        "per_page": 100,
        "page": pagina,
        "price_change_percentage": "1h,24h,7d",
        "sparkline": "true"
    }
    try:
        resposta = requests.get(url, params=params, timeout=10)
        resposta.raise_for_status()
        return resposta.json()
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return []

# Mini grafico base64 com matplotlib
def mini_grafico(lista):
    fig, ax = plt.subplots(figsize=(2, 0.5), dpi=100)
    ax.plot(lista, color='lime', linewidth=1)
    ax.axis('off')
    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"

# Barra de progresso para supply
def barra_supply(porcentagem):
    return html.Div([
        html.Div(style={
            "width": f"{porcentagem}%",
            "backgroundColor": "#00ff00",
            "height": "10px",
            "borderRadius": "5px"
        })
    ], style={
        "backgroundColor": "#444",
        "width": "100%",
        "borderRadius": "5px",
        "overflow": "hidden"
    })

# Função para construir a tabela com html.Table
def construir_tabela(dados):
    linhas = []
    for cripto in dados:
        icon_1h = "🔺" if float(cripto['1h'].replace('%','')) > 0 else "🔻"
        icon_24h = "🔺" if float(cripto['24h'].replace('%','')) > 0 else "🔻"
        icon_7d = "🔺" if float(cripto['7d'].replace('%','')) > 0 else "🔻"

        linhas.append(html.Tr([
            html.Td(cripto['rank']),
            html.Td([
                html.Img(src=cripto['image'], style={"height": "20px", "marginRight": "6px"}),
                f"{cripto['name']} ({cripto['symbol'].upper()})"
            ]),
            html.Td(cripto['preco']),
            html.Td([icon_1h, " ", cripto['1h']]),
            html.Td([icon_24h, " ", cripto['24h']]),
            html.Td([icon_7d, " ", cripto['7d']]),
            html.Td(cripto['volume']),
            html.Td([
                f"{cripto['supply']} ",
                barra_supply(cripto['supply_percent'])
            ]),
            html.Td(html.Img(src=cripto['mini_chart'], style={"height": "30px"}))
        ]))

    return html.Table([
        html.Thead(html.Tr([
            html.Th("#"), html.Th("Nome"), html.Th("Preço"), html.Th("1h %"),
            html.Th("24h %"), html.Th("7d %"), html.Th("Volume"), html.Th("Supply"),
            html.Th("Últimos 7d")
        ])),
        html.Tbody(linhas)
    ], style={
        "width": "100%",
        "color": "white",
        "backgroundColor": "#1e1e1e",
        "borderCollapse": "collapse",
        "textAlign": "center"
    })

app.layout = html.Div([
    html.H1("Painel de Criptomoedas"),
    html.P("Atualizado a cada 30 segundos", style={"textAlign": "center"}),

    html.Div([
        html.Label("Moeda de conversão:"),
        dcc.Dropdown(
            id='moeda-base',
            options=[
                {'label': 'Dólar (USD)', 'value': 'usd'},
                {'label': 'Real (BRL)', 'value': 'brl'},
                {'label': 'Euro (EUR)', 'value': 'eur'}
            ],
            value='usd',
            clearable=False
        ),
        html.Br(),
        dcc.Input(id='filtro-nome', type='text', placeholder='Filtrar por nome da moeda', debounce=True, style={"width": "100%", "padding": "10px"})
    ], style={"width": "30%", "margin": "auto", "marginBottom": "20px"}),

    html.Div(id='tabela'),

    dcc.Graph(id='grafico'),

    html.Div([
        html.Button("<<", id='primeira-pagina', n_clicks=0),
        html.Button("<", id='anterior', n_clicks=0),
        dcc.Input(id='pagina-atual', type='number', value=1, min=1, debounce=True),
        html.Button(">", id='proxima', n_clicks=0),
        html.Button(">>", id='ultima-pagina', n_clicks=0)
    ], id='paginacao', style={"display": "flex", "justifyContent": "center", "gap": "10px", "marginTop": "20px"}),

    dcc.Interval(id='intervalo', interval=30 * 1000, n_intervals=0)
])

@app.callback(
    Output('tabela', 'children'),
    [Input('moeda-base', 'value'),
     Input('pagina-atual', 'value'),
     Input('intervalo', 'n_intervals'),
     Input('filtro-nome', 'value')]
)
def atualizar_tabela(moeda, pagina, n, filtro_nome):
    dados = obter_criptos(moeda, pagina)
    simbolo = {'usd': '$', 'brl': 'R$', 'eur': '€'}.get(moeda, '')
    lista = []

    for c in dados:
        percent = min(100, (c['circulating_supply'] / (c['max_supply'] or c['circulating_supply'])) * 100) if c.get('max_supply') else 100
        item = {
            "rank": c['market_cap_rank'],
            "name": c['name'],
            "symbol": c['symbol'],
            "image": c['image'],
            "preco": f"{simbolo} {c['current_price']:,.2f}",
            "1h": f"{c['price_change_percentage_1h_in_currency']:.2f}%",
            "24h": f"{c['price_change_percentage_24h_in_currency']:.2f}%",
            "7d": f"{c['price_change_percentage_7d_in_currency']:.2f}%",
            "volume": f"{simbolo} {c['total_volume']:,.0f}",
            "supply": f"{c['circulating_supply'] / 1_000_000:.2f}M {c['symbol'].upper()}",
            "supply_percent": percent,
            "mini_chart": mini_grafico(c['sparkline_in_7d']['price'])
        }
        lista.append(item)

    if filtro_nome:
        lista = [l for l in lista if filtro_nome.lower() in l['name'].lower()]

    return construir_tabela(lista)

@app.callback(
    Output('grafico', 'figure'),
    [Input('tabela', 'children')],
    [State('pagina-atual', 'value'),
     State('moeda-base', 'value')]
)
def atualizar_grafico(_, pagina, moeda):
    return go.Figure()  # Mantido vazio por enquanto

@app.callback(
    Output('pagina-atual', 'value'),
    [Input('primeira-pagina', 'n_clicks'),
     Input('anterior', 'n_clicks'),
     Input('proxima', 'n_clicks'),
     Input('ultima-pagina', 'n_clicks')],
    State('pagina-atual', 'value')
)
def paginacao(primeira, anterior, proxima, ultima, atual):
    ctx = dash.callback_context.triggered_id
    if ctx == 'primeira-pagina':
        return 1
    elif ctx == 'anterior':
        return max(1, atual - 1)
    elif ctx == 'proxima':
        return atual + 1
    elif ctx == 'ultima-pagina':
        return 98
    return atual

if __name__ == '__main__':
    app.run(debug=True)
