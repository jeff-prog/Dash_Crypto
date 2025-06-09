# =====================================
# Painel de Criptomoedas - app.py
# Desenvolvido com Dash e CoinGecko API
# =====================================

import matplotlib
matplotlib.use('Agg')

import requests
import dash
from dash import dcc, html, Input, Output, State, ctx
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import time
import copy
import os

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap"
    ]
)
app.title = "CRYPTO WORLD"

# Força o Dash a usar o index.html personalizado na pasta assets
caminho_index = os.path.join(os.path.dirname(__file__), "assets", "index.html")
with open(caminho_index, "r", encoding="utf-8") as f:
    app.index_string = f.read()

tipo_ordenacao = {"coluna": None, "asc": True}
cache_dados = {}
cache_expiracao = 60

def obter_criptos(moeda='usd', pagina=1):
    chave = f"{moeda}-{pagina}"
    agora = time.time()
    if chave in cache_dados and (agora - cache_dados[chave]['timestamp']) < cache_expiracao:
        return cache_dados[chave]['dados']

    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": moeda,
        "order": "market_cap_desc",
        "per_page": 20,
        "page": pagina,
        "price_change_percentage": "1h,24h,7d",
        "sparkline": "true"
    }
    try:
        resposta = requests.get(url, params=params, timeout=10)
        resposta.raise_for_status()
        dados = resposta.json()
        for c in dados:
            if 'sparkline_in_7d' in c and 'mini_chart' not in c:
                c['mini_chart'] = mini_grafico(c['sparkline_in_7d']['price'])
        cache_dados[chave] = {"dados": dados, "timestamp": agora}
        return dados
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return []

def mini_grafico(lista):
    fig, ax = plt.subplots(figsize=(2.2, 0.6), dpi=100)
    x = list(range(len(lista)))
    ax.plot(x, lista, color='lime', linewidth=1)
    ax.fill_between(x, lista, color='lime', alpha=0.3)
    ax.set_xlim(min(x), max(x))
    ax.set_ylim(min(lista), max(lista) * 1.01)
    ax.axis('off')
    plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    buffer = BytesIO()
    plt.savefig(buffer, format='png', transparent=True)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"

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

def icone(variacao):
    valor = float(variacao.replace('%', ''))
    classe = "seta-verde" if valor > 0 else "seta-vermelha"
    simbolo = "▲" if valor > 0 else "▼"
    return html.Span([
        html.Span(simbolo, className=classe),
        f" {variacao}"
    ])

def construir_tabela(dados):
    linhas = []
    for cripto in dados:
        linhas.append(html.Tr([
            html.Td(cripto['rank']),
            html.Td([
                html.Img(src=cripto['image'], style={"height": "20px", "marginRight": "6px"}),
                html.Span(f"{cripto['name']} ({cripto['symbol'].upper()})")
            ]),
            html.Td(cripto['preco']),
            html.Td(icone(f"{cripto['1h_valor']:.2f}%")),
            html.Td(icone(f"{cripto['24h_valor']:.2f}%")),
            html.Td(icone(f"{cripto['7d_valor']:.2f}%")),
            html.Td(cripto['volume']),
            html.Td(cripto['marketcap']),
            html.Td([
                f"{cripto['supply']} ",
                barra_supply(cripto['supply_percent'])
            ]),
            html.Td(html.Img(src=cripto['mini_chart'], style={"height": "30px"}))
        ]))

    def th_coluna(nome, id_coluna):
        seta = " ▲" if tipo_ordenacao['coluna'] != id_coluna else (" ▲" if tipo_ordenacao['asc'] else " ▼")
        return html.Th([nome + seta], id=f"col-{id_coluna}", style={"cursor": "pointer"})

    cabecalho = html.Tr([
        th_coluna("#", "rank"),
        th_coluna("Nome", "name"),
        th_coluna("Preço", "preco_valor"),
        th_coluna("1h %", "1h_valor"),
        th_coluna("24h %", "24h_valor"),
        th_coluna("7d %", "7d_valor"),
        th_coluna("Volume", "volume_valor"),
        th_coluna("Market Cap", "marketcap_valor"),
        th_coluna("Supply", "supply_valor"),
        html.Th("Gráfico")
    ])

    return html.Table([
        html.Thead(cabecalho),
        html.Tbody(linhas)
    ], style={
        "width": "100%",
        "color": "white",
        "backgroundColor": "#1e1e1e",
        "borderCollapse": "collapse",
        "textAlign": "center"
    })

app.layout = html.Div([
    html.Script("""
        document.addEventListener('DOMContentLoaded', function () {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === "attributes" && mutation.attributeName === "data") {
                        const tema = document.querySelector('[id^="tema-selecionado"]').dataset.value;
                        document.body.className = 'modo-' + tema;
                    }
                });
            });
            const alvo = document.querySelector('[id^="tema-selecionado"]');
            if (alvo) {
                observer.observe(alvo, { attributes: true });
                const temaInicial = alvo.dataset.value || "dark";
                document.body.className = 'modo-' + temaInicial;
            }
        });
    """),

    dcc.Store(id='tema-selecionado', data='dark'),

    html.H1("CRYPTO WORLD", style={
        "marginBottom": "160px",
        "fontFamily": "'Orbitron', sans-serif",
        "fontWeight": "700",
        "letterSpacing": "2px",
        "color": "#00FF99"
    }),

    html.Div([
        html.Label("Currency:"),
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
        dcc.Input(id='filtro-nome', type='text', placeholder='Filtrar por nome da moeda', debounce=True,
                  style={"width": "100%", "padding": "10px"})
    ], style={"width": "30%", "margin": "auto", "marginBottom": "20px"}),

    html.P("Loaded every 60 seconds", style={"textAlign": "center"}),

    dcc.Store(id='dados-memoria'),
    dcc.Store(id='tema-claro', data=False),
    dcc.Store(id='ordenacao-store'),

    html.Div(id='tabela'),

    html.Div([
        html.Button("<<", id='primeira-pagina', n_clicks=0),
        html.Button("<", id='anterior', n_clicks=0),
        dcc.Input(id='pagina-atual', type='number', value=1, min=1, debounce=True),
        html.Button(">", id='proxima', n_clicks=0),
        html.Button(">>", id='ultima-pagina', n_clicks=0)
    ], style={"display": "flex", "justifyContent": "center", "gap": "10px", "marginTop": "20px"}),

    dcc.Interval(id='intervalo', interval=30 * 1000, n_intervals=0)
],
style={
    "minHeight": "100vh"
})

@app.callback(
    Output('dados-memoria', 'data'),
    [Input('moeda-base', 'value'),
     Input('pagina-atual', 'value'),
     Input('intervalo', 'n_intervals'),
     Input('filtro-nome', 'value'),
     Input('ordenacao-store', 'data')]
)
def carregar_dados(moeda, pagina, n, filtro_nome, ordenacao):
    dados = obter_criptos(moeda, pagina)
    simbolo = {'usd': '$', 'brl': 'R$', 'eur': '€'}.get(moeda, '')
    lista = []

    for c in dados:
        percent = min(100, (c['circulating_supply'] / (c['max_supply'] or c['circulating_supply'])) * 100)
        item = {
            "rank": c['market_cap_rank'],
            "name": c['name'],
            "symbol": c['symbol'],
            "image": c['image'],
            "preco": f"{simbolo} {c['current_price']:,.2f}",
            "1h_valor": c['price_change_percentage_1h_in_currency'],
            "24h_valor": c['price_change_percentage_24h_in_currency'],
            "7d_valor": c['price_change_percentage_7d_in_currency'],
            "volume": f"{simbolo} {c['total_volume']:,.0f}",
            "marketcap": f"{simbolo} {c['market_cap']:,.0f}",
            "supply": f"{c['circulating_supply'] / 1_000_000:.2f}M {c['symbol'].upper()}",
            "supply_percent": percent,
            "mini_chart": c.get("mini_chart", ""),
            "preco_valor": c['current_price'],
            "volume_valor": c['total_volume'],
            "marketcap_valor": c['market_cap'],
            "supply_valor": c['circulating_supply']
        }
        lista.append(item)

    if filtro_nome:
        lista = [l for l in lista if filtro_nome.lower() in l['name'].lower()]

    if ordenacao and 'coluna' in ordenacao:
        lista.sort(key=lambda x: x[ordenacao['coluna']], reverse=not ordenacao['asc'])

    return lista

@app.callback(
    Output('tabela', 'children'),
    Input('dados-memoria', 'data'),
    Input('ordenacao-store', 'data')
)
def atualizar_tabela(dados, ordenacao):
    if not dados:
        return "Sem dados"
    dados = copy.deepcopy(dados)
    if ordenacao and 'coluna' in ordenacao:
        tipo_ordenacao.update(ordenacao)
        coluna = ordenacao['coluna']
        dados.sort(key=lambda x: x[coluna], reverse=not ordenacao['asc'])
    return construir_tabela(dados)

@app.callback(
    Output('ordenacao-store', 'data'),
    [Input(f'col-{col}', 'n_clicks') for col in [
        'rank', 'name', 'preco_valor', '1h_valor', '24h_valor', '7d_valor',
        'volume_valor', 'marketcap_valor', 'supply_valor']]
)
def ordenar_tabela(*args):
    colunas = ['rank', 'name', 'preco_valor', '1h_valor', '24h_valor',
               '7d_valor', 'volume_valor', 'marketcap_valor', 'supply_valor']
    for i, n in enumerate(args):
        if ctx.triggered_id == f'col-{colunas[i]}':
            if tipo_ordenacao['coluna'] == colunas[i]:
                return {"coluna": colunas[i], "asc": not tipo_ordenacao['asc']}
            return {"coluna": colunas[i], "asc": True}
    return dash.no_update

@app.callback(
    Output('pagina-atual', 'value'),
    [Input('primeira-pagina', 'n_clicks'),
     Input('anterior', 'n_clicks'),
     Input('proxima', 'n_clicks'),
     Input('ultima-pagina', 'n_clicks')],
    State('pagina-atual', 'value')
)
def paginacao(primeira, anterior, proxima, ultima, atual):
    acao = ctx.triggered_id
    if acao == 'primeira-pagina':
        return 1
    elif acao == 'anterior':
        return max(1, atual - 1)
    elif acao == 'proxima':
        return atual + 1
    elif acao == 'ultima-pagina':
        return 98
    return atual

@app.callback(
    Output('tema-selecionado', 'data'),
    Input('seletor-tema', 'value')
)
def mudar_tema(valor):
    return valor

if __name__ == '__main__':
    app.run(debug=True)
