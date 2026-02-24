FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc
RUN pip install --no-cache-dir discord.py yfinance mplfinance pandas python-dotenv google-genai
COPY bot.py .
CMD ["python", "-u", "bot.py"]
