import yfinance as yf
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from fpdf import FPDF
import matplotlib.pyplot as plt
from mistralai import Mistral
import datetime
import os

# --- CONFIGURATION ---
TICKER = "AAPL"  # Marche avec BTC-USD, LMT, etc.
API_KEY = "BT9wVAi9dwpWMgQNZCxWgH3xQXlK9GVA"
client = Mistral(api_key=API_KEY)

# --- STEP 1: DATA FETCHING ---
def fetch_stock_data(ticker):
    print(f"📥 Récupération des données pour {ticker}...")
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y")
    info = stock.info
    return df, info

# --- STEP 2: TECHNICAL ANALYSIS ---
def calculate_technicals(df):
    print("📈 Calcul des indicateurs techniques...")
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def generate_chart(df, ticker):
    print("🎨 Génération du graphique haute résolution...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot Prix
    ax1.plot(df.index, df['Close'], label='Prix de Clôture', color='#1f77b4', linewidth=1.5)
    ax1.plot(df.index, df['SMA_50'], label='SMA 50', linestyle='--', color='#ff7f0e', alpha=0.8)
    ax1.plot(df.index, df['SMA_200'], label='SMA 200', linestyle='-', color='#d62728', alpha=0.8)
    ax1.set_title(f"Analyse Technique : {ticker}", fontsize=16, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot RSI
    ax2.plot(df.index, df['RSI'], label='RSI (14)', color='#9467bd')
    ax2.axhline(70, linestyle='--', color='red', alpha=0.5)
    ax2.axhline(30, linestyle='--', color='green', alpha=0.5)
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    plt.savefig("chart.png", dpi=300)
    plt.close()

# --- STEP 3: NEWS ---
def get_news(ticker):
    print(f"📰 Scan des dernières actualités...")
    stock = yf.Ticker(ticker)
    news = stock.news[:5]
    headlines = []
    for item in news:
        headlines.append(f"- {item['title']}")
    return "\n".join(headlines) if headlines else "Aucune actualité récente trouvée."

# --- STEP 4: MISTRAL AI ---
def analyze_with_mistral(ticker, df, news_summary, info):
    print("🧠 Analyse stratégique par Mistral AI...")
    
    last = df.iloc[-1]
    quote_type = info.get('quoteType', 'EQUITY')
    
    prompt = f"""
    Role: Senior Hedge Fund Analyst.
    Asset: {ticker} ({quote_type}).
    Price: ${last['Close']:.2f}
    RSI: {last['RSI']:.2f}
    SMA 50/200: {last['SMA_50']:.2f} / {last['SMA_200']:.2f}
    
    Recent News:
    {news_summary}
    
    Task:
    Provide a professional institutional-grade analysis.
    Structure: 
    1. Market Sentiment & Trend
    2. Key Catalysts
    3. Risk Factors
    4. Trading Verdict (Cash-only, no leverage) with Entry, Target, and Stop-Loss.
    """
    
    try:
        chat_response = client.chat.complete(
            model="mistral-tiny",
            messages=[{"role": "user", "content": prompt}]
        )
        return chat_response.choices[0].message.content
    except Exception as e:
        return f"Erreur API: {e}"

# --- STEP 5: PDF REPORTING ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(100)
        self.cell(0, 10, 'QUANT COUNCIL - INSTITUTIONAL REPORT', 0, 1, 'C')
        self.ln(5)

def create_pdf(ticker, analysis_text):
    print("📄 Construction du rapport PDF...")
    pdf = PDF()
    pdf.add_page()
    
    # Titre
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(30, 45, 110) # Bleu Marine
    pdf.cell(0, 15, f"Rapport d'Analyse : {ticker}", ln=True, align='L')
    
    # Date
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(128)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.cell(0, 10, f"Généré le : {date_str}", ln=True, align='L')
    pdf.ln(5)

    # Graphique
    if os.path.exists("chart.png"):
        pdf.image("chart.png", x=10, w=190)
    
    # Analyse
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(30, 45, 110)
    pdf.cell(0, 10, "Intelligence Artificielle & Verdict", ln=True)
    
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(0)
    
    # Nettoyage des caractères pour éviter les crashs PDF
    clean_text = analysis_text.replace('$', '\$').replace('€', 'EUR')
    clean_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 7, clean_text)
    
    filename = f"Report_{ticker}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
    pdf.output(filename)
    return filename

# --- MAIN ---
def main():
    df, info = fetch_stock_data(TICKER)
    df = calculate_technicals(df)
    generate_chart(df, TICKER)
    news = get_news(TICKER)
    
    analysis = analyze_with_mistral(TICKER, df, news, info)
    
    filename = create_pdf(TICKER, analysis)
    print(f"\n✅ Terminé ! Rapport disponible : {filename}")
    
    # Ouvre le dossier automatiquement (Windows)
    if os.name == 'nt':
        os.startfile('.')

if __name__ == "__main__":
    main()