# 🪙 Dash Crypto

Este projeto é um painel interativo feito com [Dash](https://dash.plotly.com/) e [Plotly](https://plotly.com/python/) que exibe criptomoedas em tempo real utilizando a API da CoinGecko.

## 🔥 Funcionalidades

- Tabela com as top 100 criptomoedas (paginadas)
- Mini gráfico dos últimos 7 dias por moeda (tipo CoinMarketCap)
- Variação de preço (1h, 24h, 7d) com ícones 🔺/🔻
- Barra de progresso visual no Circulating Supply
- Filtro por nome da moeda
- Gráfico principal com histórico da moeda (em breve)

## 🚀 Como rodar o projeto

```bash
git clone https://github.com/jeff-prog/Dash_Crypto.git
cd Dash_Crypto
python -m venv .venv
source .venv/Scripts/activate     # Windows
pip install -r requirements.txt
python app.py
