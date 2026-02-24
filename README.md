# Institutional Desk Discord Bot 

*[Version Française disponible plus bas / French version below]*

A Discord bot designed to act as a Hedge Fund Quantitative Analyst. It filters market noise, tracks smart money, and provides actionable, data-driven insights directly in your Discord server.

## Core Philosophy: Risk Management First
Built around a strict **cash-only** mandate, the AI engine is hardcoded to reject any strategies involving leverage, short-selling, or options buying (Puts/Calls). Capital preservation is the absolute priority, and the bot will actively advise users to stay in cash during bearish regimes rather than taking reckless risks.

## Key Features

* **Terminal Data Generation:** Type any ticker (e.g., `AAPL`, `BTC`, `SPY`) to instantly generate a comprehensive financial terminal. Includes a custom candlestick chart (with SMA 50/200 & RSI), fundamental valuation, and technical trends.
* **Smart Money Tracking:** Monitors institutional order flows, including Insider Trading (Buying/Selling), Options Put/Call Ratios, and abnormal "Whale" volume Z-Scores.
* **Advanced Risk Metrics:** Calculates Volatility Squeeze (Bollinger Band compression) for breakout detection and 1-Year Maximum Drawdown (MAX DD) to assess real downside risk.
* **Autonomous Daily Scanner:** A built-in cron job runs every 24 hours to scan a custom Watchlist, alerting the server to extreme market anomalies (e.g., RSI < 30, Whale Volume > 2.5).
* **Contextual AI Chatbot:** Powered by Google Gemini (2.5 Flash), the bot remembers the last 5 terminal scans or alerts. You can converse naturally with the bot about recently scanned assets. It features strict anti-hallucination protocols: if an asset is not in its short-term memory, it will demand a fresh scan rather than inventing data.

## Technical Stack
* **Python 3.11+**
* **Discord.py:** For Discord API integration.
* **yfinance & pandas:** For real-time market data fetching and quantitative calculations.
* **mplfinance:** For generating high-resolution technical charts.
* **Google Gemini (`gemini-2.5-flash`):** For lightning-fast natural language processing and institutional memo generation via the `google-genai` SDK.
* **Docker & Docker Compose:** For robust, 24/7 containerized deployment.

## Installation & Deployment

1. **Clone the repository and navigate to the folder.**
2. **Create a `.env` file** in the root directory and add your API keys:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ALERT_CHANNEL_ID=your_discord_channel_id_for_scanner_alerts

```

3. **Deploy using Docker:**
```bash
sudo docker-compose up -d --build

```



## Command Reference

* `[TICKER]` : Generates the Data Terminal (e.g., `MSFT`, `TSLA`). Autocorrects common typos.
* `!forcescan` : Manually triggers the institutional anomaly scanner.
* `!add [TICKER]` : Adds an asset to the autonomous scanner's watchlist.
* `!remove [TICKER]` : Removes an asset from the watchlist.
* `!list` : Displays the current watchlist.

---

---

# Bot Discord Institutionnel

Un bot Discord conçu pour agir comme un analyste quantitatif de Hedge Fund. Il filtre le bruit du marché, traque la "Smart Money" et fournit des analyses basées sur les données directement sur votre serveur Discord.

## Philosophie Centrale : La Gestion du Risque

Construit autour d'un mandat strictement **Cash-Only**, le moteur de l'IA est programmé pour rejeter toute stratégie impliquant des effets de levier, de la vente à découvert (Short) ou l'achat d'options. La préservation du capital est la priorité absolue : le bot conseillera activement de rester en liquidités (Cash) lors des régimes baissiers plutôt que de prendre des risques démesurés.

## Fonctionnalités Principales

* **Terminal de Données :** Tapez n'importe quel symbole (ex: `AAPL`, `BTC`, `SPY`) pour générer instantanément un terminal financier complet. Inclut un graphique en chandeliers (avec SMA 50/200 & RSI), la valorisation fondamentale et les tendances techniques.
* **Traçage de la "Smart Money" :** Surveille les flux institutionnels, incluant les délits d'initiés légaux (Achats/Ventes des dirigeants), les ratios Put/Call sur les options, et les anomalies de volume des "Baleines" (Z-Score).
* **Métriques de Risque Avancées :** Calcule la compression de volatilité (Squeeze des bandes de Bollinger) pour détecter les cassures imminentes, ainsi que le Drawdown Maximal (MAX DD) sur 1 an pour évaluer le risque de perte réel.
* **Scanner Autonome Quotidien :** Une tâche de fond (cron job) s'exécute toutes les 24h pour scanner une Watchlist personnalisée, alertant le serveur des anomalies extrêmes du marché (ex: RSI < 30, Volume Baleine > 2.5).
* **Chatbot IA Contextuel :** Propulsé par Google Gemini (2.5 Flash), le bot se souvient des 5 derniers scans ou alertes. Vous pouvez converser naturellement avec lui sur les actifs récemment analysés. Il intègre des protocoles anti-hallucination stricts : si un actif n'est pas dans sa mémoire à court terme, il exigera un nouveau scan plutôt que d'inventer des données.

## Stack Technique

* **Python 3.11+**
* **Discord.py :** Pour l'intégration de l'API Discord.
* **yfinance & pandas :** Pour la récupération des données de marché en temps réel et les calculs quantitatifs.
* **mplfinance :** Pour la génération de graphiques techniques haute résolution.
* **Google Gemini (`gemini-2.5-flash`) :** Pour le traitement ultra-rapide du langage naturel et la rédaction des mémos institutionnels (via le SDK `google-genai`).
* **Docker & Docker Compose :** Pour un déploiement conteneurisé robuste tournant 24h/24 et 7j/7.

## Installation & Déploiement

1. **Clonez le dépôt et naviguez dans le dossier.**
2. **Créez un fichier `.env**` à la racine et ajoutez vos clés API :
```env
DISCORD_TOKEN=votre_token_discord_ici
GEMINI_API_KEY=votre_cle_api_gemini_ici
ALERT_CHANNEL_ID=id_du_salon_discord_pour_les_alertes

```


3. **Déployez avec Docker :**
```bash
sudo docker-compose up -d --build

```



## Liste des Commandes

* `[TICKER]` : Génère le Terminal de Données (ex: `MSFT`, `TSLA`). Corrige automatiquement les fautes de frappe courantes.
* `!forcescan` : Déclenche manuellement le radar d'anomalies institutionnelles.
* `!add [TICKER]` : Ajoute un actif à la Watchlist du scanner autonome.
* `!remove [TICKER]` : Retire un actif de la Watchlist.
* `!list` : Affiche la Watchlist actuelle.
