import discord
from discord.ext import commands, tasks
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import io
import asyncio
import json
import os
import datetime
from google import genai
import re
from collections import deque
from dotenv import load_dotenv

# --- SÉCURITÉ & CONFIGURATION ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ALERT_CHANNEL_ID = int(os.getenv("ALERT_CHANNEL_ID", 0))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration de la NOUVELLE API Gemini
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# --- MÉMOIRE & WATCHLIST ---
CHAT_HISTORY = {} 
WATCHLIST_FILE = "watchlist.json"

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    return ["AAPL", "MSFT", "NVDA", "TSLA", "BTC-USD", "SPY"]

def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(watchlist, f)

COMMON_TYPOS = {
    "APPL": "AAPL", "APPLE": "AAPL", 
    "FB": "META", "FACEBOOK": "META", 
    "TWTR": "X", "TWITTER": "X", 
    "GOOGLE": "GOOGL", "ALPHABET": "GOOGL", "GOOG": "GOOGL",
    "TESLA": "TSLA", "TELSLA": "TSLA",
    "MICROSOFT": "MSFT", "MACROSOFT": "MSFT",
    "NVIDIA": "NVDA", "NVDIA": "NVDA",
    "AMAZON": "AMZN", "AMZ": "AMZN",
    "NETFLIX": "NFLX",
    "AMD": "AMD", "ADVANCED MICRO DEVICES": "AMD",
    "INTEL": "INTC",
    "TSMC": "TSM", "TAIWAN SEMI": "TSM",
    "DISNEY": "DIS", "WALT DISNEY": "DIS",
    "PALANTIR": "PLTR",
    "COINBASE": "COIN",
    "UBER": "UBER", "AIRBNB": "ABNB",
    "SPOTIFY": "SPOT", "SHOPIFY": "SHOP",
    "PAYPAL": "PYPL", "SQUARE": "SQ", "BLOCK": "SQ",
    "GAMESTOP": "GME", "AMC": "AMC",
    "ALIBABA": "BABA", "BABA": "BABA",
    "NIO": "NIO", "RIVIAN": "RIVN", "LUCID": "LCID",
    "BRK.B": "BRK-B", "BRKB": "BRK-B", "BERKSHIRE": "BRK-B",
    "BTC": "BTC-USD", "BITCOIN": "BTC-USD", 
    "ETH": "ETH-USD", "ETHEREUM": "ETH-USD", 
    "XRP": "XRP-USD", "RIPPLE": "XRP-USD",
    "SOL": "SOL-USD", "SOLANA": "SOL-USD",
    "ADA": "ADA-USD", "CARDANO": "ADA-USD",
    "DOGE": "DOGE-USD", "DOGECOIN": "DOGE-USD",
    "SHIB": "SHIB-USD", "SHIBA": "SHIB-USD",
    "DOT": "DOT-USD", "POLKADOT": "DOT-USD",
    "LINK": "LINK-USD", "CHAINLINK": "LINK-USD",
    "AVAX": "AVAX-USD", "AVALANCHE": "AVAX-USD",
    "MATIC": "MATIC-USD", "POL": "MATIC-USD", "POLYGON": "MATIC-USD",
    "LTC": "LTC-USD", "LITECOIN": "LTC-USD",
    "BNB": "BNB-USD", "BINANCE": "BNB-USD",
    "SPX": "^GSPC", "S&P500": "SPY", "S&P": "SPY", 
    "NDX": "^NDX", "NASDAQ": "QQQ", 
    "VIX": "^VIX", "VOLATILITY": "^VIX",
    "DOW": "^DJI", "DOWJONES": "DIA",
    "RUT": "^RUT", "RUSSELL": "IWM",
    "GOLD": "GLD", "SILVER": "SLV"
}

# --- OUTILS FINANCIERS AVANCÉS ---
def create_ascii_bar(value, max_val=100, length=10):
    try:
        val = int(value)
        filled = int((val / max_val) * length)
        return f"[`{'█' * filled}{'░' * (length - filled)}`]"
    except: return "[`░░░░░░░░░░`]"

def get_market_context():
    try:
        spy = yf.Ticker("SPY").history(period="1y")
        vix = yf.Ticker("^VIX").history(period="1d")
        if spy.empty or vix.empty: return "Unknown"
        trend = "BULLISH 🟢" if spy['Close'].iloc[-1] > spy['Close'].rolling(200).mean().iloc[-1] else "BEARISH 🔴"
        return f"SPY: {trend} | VIX: {vix['Close'].iloc[-1]:.2f}"
    except: return "Macro N/A"

def get_smart_money_data(stock, quote_type):
    insider_status = "⚪ NEUTRAL"
    pc_ratio = "N/A"
    earnings_date = "N/A"
    
    if quote_type == "EQUITY":
        try:
            ins = stock.insider_transactions
            if ins is not None and not ins.empty:
                recent = ins.head(10)
                buys = recent[recent['Text'].str.contains("Purchase", case=False, na=False)].shape[0]
                sells = recent[recent['Text'].str.contains("Sale", case=False, na=False)].shape[0]
                if buys > sells: insider_status = "🟢 BUYING"
                elif sells > buys + 2: insider_status = "🔴 SELLING"
        except: pass
        
        try:
            dates = stock.options
            if dates:
                opt = stock.option_chain(dates[0])
                vol_c = opt.calls['volume'].sum()
                vol_p = opt.puts['volume'].sum()
                if vol_c > 0: pc_ratio = f"{vol_p / vol_c:.2f}"
        except: pass
        
        try:
            cal = stock.calendar
            if cal and 'Earnings Date' in cal:
                edate = cal['Earnings Date'][0]
                if pd.notna(edate): earnings_date = edate.strftime('%Y-%m-%d')
        except: pass

    return insider_status, pc_ratio, earnings_date

def calculate_metrics(stock, df):
    info = stock.info
    last = df.iloc[-1]
    quote_type = info.get('quoteType', 'EQUITY')
    
    df['SMA200'] = df['Close'].rolling(200).mean()
    sma_200 = df['SMA200'].iloc[-1] if not pd.isna(df['SMA200'].iloc[-1]) else last['Close']
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/loss)).iloc[-1]
    rsi = rsi if not pd.isna(rsi) else 50
    
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['STD20'] = df['Close'].rolling(20).std()
    bb_width = ((df['SMA20'] + 2*df['STD20']) - (df['SMA20'] - 2*df['STD20'])) / df['SMA20']
    is_squeeze = bb_width.iloc[-1] < 0.05 
    
    max_dd = (df['Close'] / df['Close'].cummax() - 1).min() * 100
    
    vol_mean = df['Volume'].rolling(20).mean().iloc[-1]
    vol_std = df['Volume'].rolling(20).std().iloc[-1]
    z_score = (last['Volume'] - vol_mean) / vol_std if vol_std else 0

    metrics = {
        "QuoteType": quote_type, "Price": last['Close'],
        "Trend": "UP 🐂" if last['Close'] > sma_200 else "DOWN 🐻",
        "RSI": rsi, "Whale_Z": z_score, "Squeeze": is_squeeze, "MaxDD": max_dd,
        "Sector": info.get('sector', 'N/A')
    }

    if quote_type == "CRYPTOCURRENCY":
        metrics["MarketCap"] = info.get('marketCap', 0)
        metrics["Volume24h"] = info.get('volume24Hr', 0)
    elif quote_type == "ETF":
        metrics["Yield"] = info.get('yield', 0) * 100 if info.get('yield') else 0
        metrics["ExpenseRatio"] = info.get('totalAssets', 0) 
    else:
        metrics["Inst_Own"] = info.get('heldPercentInstitutions', 0) * 100 if info.get('heldPercentInstitutions') else 0
        metrics["PE"] = info.get('trailingPE', 0)
        eps, book = info.get('trailingEps', 0), info.get('bookValue', 0)
        metrics["Fair_Val"] = (22.5 * eps * book) ** 0.5 if (eps > 0 and book > 0) else 0

    return metrics

def generate_pro_chart(df, ticker):
    buf = io.BytesIO()
    df['SMA50'] = df['Close'].rolling(50).mean()
    df['SMA200'] = df['Close'].rolling(200).mean()
    delta = df['Close'].diff()
    df['RSI'] = 100 - (100 / (1 + (delta.where(delta > 0, 0)).rolling(14).mean() / (-delta.where(delta < 0, 0)).rolling(14).mean()))
    
    plot_df = df.tail(126) 
    s = mpf.make_mpf_style(marketcolors=mpf.make_marketcolors(up='#00ff00', down='#ff0000', edge='inherit', wick='inherit', volume='in'), base_mpf_style='nightclouds', gridstyle=':')
    
    apds = []
    if not plot_df['SMA50'].isna().all(): apds.append(mpf.make_addplot(plot_df['SMA50'], color='cyan', width=0.8, panel=0))
    if not plot_df['SMA200'].isna().all(): apds.append(mpf.make_addplot(plot_df['SMA200'], color='orange', width=0.8, panel=0))
    if not plot_df['RSI'].isna().all(): apds.append(mpf.make_addplot(plot_df['RSI'], panel=2, color='white', width=0.8, ylabel='RSI', ylim=(0,100)))
    
    kwargs = dict(type='candle', style=s, title=f"\n{ticker} - Terminal", volume=True, panel_ratios=(6, 2, 2), savefig=dict(fname=buf, dpi=100, bbox_inches='tight'), figsize=(10, 6))
    if apds: kwargs['addplot'] = apds
        
    mpf.plot(plot_df, **kwargs)
    buf.seek(0)
    return discord.File(buf, filename=f"{ticker}_chart.png")

# --- COMMANDES ---
@bot.command(name="add")
async def add_to_watchlist(ctx, ticker: str):
    ticker = ticker.upper()
    if ticker in COMMON_TYPOS: ticker = COMMON_TYPOS[ticker]
    w = load_watchlist()
    if ticker not in w: w.append(ticker); save_watchlist(w); await ctx.send(f"✅ **{ticker}** ajouté.")
    else: await ctx.send(f"⚠️ **{ticker}** déjà présent.")

@bot.command(name="remove")
async def remove_from_watchlist(ctx, ticker: str):
    ticker = ticker.upper()
    if ticker in COMMON_TYPOS: ticker = COMMON_TYPOS[ticker]
    w = load_watchlist()
    if ticker in w: w.remove(ticker); save_watchlist(w); await ctx.send(f"🗑️ **{ticker}** retiré.")

@bot.command(name="list")
async def show_watchlist(ctx):
    await ctx.send(f"📋 **Watchlist :** " + ", ".join(load_watchlist()))

@bot.command(name="forcescan")
async def force_scan(ctx):
    await ctx.send("🛠️ **Scanner d'Anomalies...**")
    await daily_scanner()

# --- SCANNER AUTONOME ---
@tasks.loop(hours=24)
async def daily_scanner():
    if ALERT_CHANNEL_ID == 0: return
    channel = bot.get_channel(ALERT_CHANNEL_ID)
    if not channel: return

    watchlist = load_watchlist()
    anomalies = []

    def scan():
        for ticker in watchlist:
            try:
                stock = yf.Ticker(ticker)
                df = stock.history(period="1y")
                if df.empty: continue
                metrics = calculate_metrics(stock, df)
                insider, _, earnings = get_smart_money_data(stock, metrics["QuoteType"])
                
                reasons = []
                if metrics["Whale_Z"] > 2.5: reasons.append(f"🐳 Whale Vol (Z: {metrics['Whale_Z']:.1f})")
                if metrics["RSI"] < 30: reasons.append(f"📉 Oversold (RSI: {metrics['RSI']:.1f})")
                if metrics["Squeeze"]: reasons.append("🗜️ VOL SQUEEZE (Breakout Risk)")
                if "BUYING" in insider: reasons.append("🟢 Insider Buying")
                
                if earnings != "N/A":
                    try:
                        days = (datetime.datetime.strptime(earnings, "%Y-%m-%d").date() - datetime.date.today()).days
                        if 0 <= days <= 7: reasons.append(f"⚠️ Earnings in {days}d")
                    except: pass
                    
                if reasons: anomalies.append(f"**{ticker}** (${metrics['Price']:.2f}) ➔ " + " | ".join(reasons))
            except: continue

    await asyncio.to_thread(scan)
    
    if anomalies:
        report = "\n".join(anomalies)
        embed = discord.Embed(title="🚨 Institutional Radar", description=report, color=0xFFD700)
        await channel.send(embed=embed)
        if ALERT_CHANNEL_ID not in CHAT_HISTORY: CHAT_HISTORY[ALERT_CHANNEL_ID] = deque(maxlen=5)
        CHAT_HISTORY[ALERT_CHANNEL_ID].append(f"[SCANNER]: {report}")

@daily_scanner.before_loop
async def before_daily_scanner():
    await bot.wait_until_ready()

# --- CHATBOT GEMINI ---
async def handle_conversation(message):
    history = CHAT_HISTORY.get(message.channel.id, [])
    context = "Aucune data." if not history else "\n".join(history)
    
    async with message.channel.typing():
        prompt = f"""
        Tu es le "Quant Council", trader senior. Contexte de notre session : {context}
        Question du client : "{message.content}"
        
        RÈGLES ABSOLUES :
        1. SOIS BREF. 4 phrases MAX. Zéro blabla. Va droit au but.
        2. Si l'actif n'est pas dans le contexte, dis EXACTEMENT: "Aucune data en cache. Tape le symbole (ex: MSFT) pour lancer le terminal." Ne justifie pas.
        3. LONG OU CASH SEULEMENT. INTERDICTION STRICTE DE PROPOSER DU SHORT, DES PUTS, OU DE LA VENTE A DECOUVERT. Si la situation est mauvaise, dis "RESTER EN CASH" ou "EVITER".
        """
        try:
            response = await asyncio.to_thread(gemini_client.models.generate_content, model='gemini-2.5-flash', contents=prompt)
            reply_text = response.text
            if len(reply_text) > 800: reply_text = reply_text[:800] + "...\n*(Réponse tronquée pour concision)*"
            await message.reply(reply_text.strip())
        except Exception as e:
            print(f"Erreur Gemini Chat: {e}", flush=True)
            await message.reply("❌ Erreur API Gemini.")

async def run_analysis(message, ticker_input):
    ticker = ticker_input.upper().strip()
    if ticker in COMMON_TYPOS: ticker = COMMON_TYPOS[ticker]
        
    await message.add_reaction("⚡")
    status_msg = await message.channel.send(f"🔄 **Terminal : {ticker}...**")

    try:
        def fetch_data():
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            used_ticker = ticker
            if df.empty and "-" not in ticker:
                used_ticker = f"{ticker}-USD"
                stock = yf.Ticker(used_ticker)
                df = stock.history(period="1y")

            if df.empty or len(df) < 30: return None

            metrics = calculate_metrics(stock, df)
            macro = get_market_context()
            insider, pc_ratio, earnings = get_smart_money_data(stock, metrics["QuoteType"])
            
            info = stock.info
            desc = info.get('longBusinessSummary', info.get('description', ''))
            if len(desc) < 10: desc = f"N/A. INVENT 1 SHORT SENTENCE DESCRIBING {used_ticker}."
            else: desc = desc[:1000] + "..."
            
            chart = generate_pro_chart(df, used_ticker)
            return metrics, macro, insider, pc_ratio, earnings, desc, chart, used_ticker

        data = await asyncio.to_thread(fetch_data)
        if not data: return await status_msg.edit(content=f"❌ Erreur Data `{ticker}`.")

        metrics, macro, insider, pc_ratio, earnings, desc, chart, final_ticker = data
        
        prompt = f"""
        Role: Quant Desk Manager. Asset: {final_ticker} ({metrics['QuoteType']}).
        Macro: {macro} | Price: ${metrics['Price']:.2f} | RSI: {metrics['RSI']:.1f} | Drawdown: {metrics['MaxDD']:.1f}%
        Squeeze: {metrics['Squeeze']} | P/C Ratio: {pc_ratio} (Note: <0.7 is bullish/optimistic, >1.0 is bearish/fear) | Insider: {insider} | Earnings: {earnings}
        Desc: {desc}
        
        RULES (CRITICAL):
        1. NO SHORT SELLING. NO PUTS. LONG OR CASH ONLY. If bearish, you MUST say "AVOID" or "STAY IN CASH".
        2. Format exactly as requested below. DO NOT USE MARKDOWN (NO ASTERISKS) for headers.

        OUTPUT FORMAT:
        [SENTIMENT]: 0-100
        [POLITICAL]: 0-10
        [SUMMARY]: 2 sentences max.
        [THESIS]: 1 sentence punchline.
        [DRIVERS]: 2 short bullets.
        [RISKS]: 2 short bullets.
        [VERDICT]: Action (Buy/Hold/Avoid/Cash), Target, Stop-Loss.
        """
        
        response = await asyncio.to_thread(gemini_client.models.generate_content, model='gemini-2.5-flash', contents=prompt)
        ai_full = response.text
        
        # Parsing Anti-Casse
        sent_val, pol_str, ai_profile = 50, "5", "Profile indisponible."
        if m := re.search(r'\[SENTIMENT\]:\s*(\d+)', ai_full, re.I): sent_val = int(m.group(1))
        if m := re.search(r'\[POLITICAL\]:\s*(\d+)', ai_full, re.I): pol_str = m.group(1)
        if m := re.search(r'\[SUMMARY\]:\s*(.*?)(?=\[THESIS\]|\Z)', ai_full, re.I | re.DOTALL): ai_profile = m.group(1).strip()
            
        # Formatage propre pour Discord
        ai_clean = ai_full
        ai_clean = re.sub(r'\[SENTIMENT\].*\n?', '', ai_clean, flags=re.I)
        ai_clean = re.sub(r'\[POLITICAL\].*\n?', '', ai_clean, flags=re.I)
        ai_clean = re.sub(r'\[SUMMARY\].*?(?=\[THESIS\]|\Z)', '', ai_clean, flags=re.I | re.DOTALL).strip()
        ai_clean = ai_clean.replace('[THESIS]:', '**THESIS:**')
        ai_clean = ai_clean.replace('[DRIVERS]:', '**DRIVERS:**')
        ai_clean = ai_clean.replace('[RISKS]:', '**RISKS:**')
        ai_clean = ai_clean.replace('[VERDICT]:', '**VERDICT:**')

        # Update Memory 
        cid = message.channel.id
        if cid not in CHAT_HISTORY: CHAT_HISTORY[cid] = deque(maxlen=5)
        CHAT_HISTORY[cid].append(f"[{final_ticker}]: P=${metrics['Price']:.2f}, RSI={metrics['RSI']:.1f}, Info: {ai_profile[:100]}...")

        # Embed UI
        embed = discord.Embed(title=f"💠 {final_ticker} | Institutional Desk", color=0x2b2d31)
        embed.set_author(name=f"Macro: {macro}", icon_url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
        embed.description = f"*{ai_profile}*"
        
        col1 = f"`PRICE `: ${metrics['Price']:.2f}\n`TREND `: {metrics['Trend']}\n`RSI   `: {metrics['RSI']:.1f}"
        if metrics['Squeeze']: col1 += "\n`SQUEZ `: ⚠️ YES"
        
        if metrics['QuoteType'] == "CRYPTOCURRENCY":
            col2 = f"`CAP   `: ${metrics.get('MarketCap',0)/1e9:.1f}B\n`VOL24 `: ${metrics.get('Volume24h',0)/1e9:.1f}B\n`MAX DD`: {metrics['MaxDD']:.1f}%"
            col3 = f"`WHALE `: {metrics['Whale_Z']:.2f}\n`P/C   `: N/A\n`EARN  `: N/A"
        elif metrics['QuoteType'] == "ETF":
            col2 = f"`YIELD `: {metrics.get('Yield',0):.2f}%\n`ASSETS`: ${metrics.get('ExpenseRatio',0)/1e9:.1f}B\n`MAX DD`: {metrics['MaxDD']:.1f}%"
            col3 = f"`WHALE `: {metrics['Whale_Z']:.2f}\n`P/C   `: {pc_ratio}\n`EARN  `: N/A"
        else:
            col2 = f"`FAIR  `: ${metrics.get('Fair_Val',0):.2f}\n`P/E   `: {metrics.get('PE',0):.1f}x\n`MAX DD`: {metrics['MaxDD']:.1f}%"
            col3 = f"`WHALE `: {metrics['Whale_Z']:.2f}\n`P/C   `: {pc_ratio}\n`EARN  `: {earnings}"

        embed.add_field(name="📈 Techs", value=col1, inline=True)
        embed.add_field(name="💰 Value / Risk", value=col2, inline=True)
        embed.add_field(name="🧠 Flow / Events", value=col3, inline=True)
        embed.add_field(name="📊 Quant Scores", value=f"`SENTIMENT:` {create_ascii_bar(sent_val)} {sent_val} | `POL RISK:` {pol_str}/10", inline=False)

        embed_memo = discord.Embed(color=0x5865F2, description=ai_clean)
        embed_memo.set_footer(text="Pollux bloomberg terminal (Powered by Gemini)")

        await status_msg.delete()
        await message.channel.send(file=chart, embed=embed)
        await message.channel.send(embed=embed_memo)

    except Exception as e:
        await status_msg.edit(content="❌ Crash interne de génération.")
        print(f"ERROR: {e}", flush=True)

@bot.event
async def on_message(msg):
    if msg.author == bot.user: return
    if msg.author.bot: return

    if msg.content.startswith('!'): 
        return await bot.process_commands(msg)
    
    words = msg.content.strip().split()
    if len(words) == 1 and re.match(r'^[A-Z0-9-.]{2,10}$', msg.content.upper()) and msg.content.upper() not in ["WHY", "HOW", "WHAT", "TEST"]:
        await run_analysis(msg, msg.content)
    else:
        await handle_conversation(msg)

@bot.event
async def on_ready():
    print(f"✅ V23 GEMINI Online: {bot.user}")
    daily_scanner.start()

bot.run(DISCORD_TOKEN)
