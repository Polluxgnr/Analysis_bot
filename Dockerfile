FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc
RUN pip install --no-cache-dir discord.py yfinance mplfinance mistralai pandas python-dotenv
COPY bot.py .
CMD ["python", "-u", "bot.py"]