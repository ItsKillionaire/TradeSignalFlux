#!/usr/bin/env python3

import os
import re
import time
import signal
import hashlib
import logging
from datetime import datetime
from typing import Set, Dict, Optional

import yaml
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

def load_config(config_path="config/config.yaml") -> Dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def setup_logging(log_file: str):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )

class TradingBot:
    def __init__(self, config: Dict):
        self.config = config
        self.session = requests.Session()
        self.processed_articles: Set[str] = set()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)

    def _shutdown_handler(self, signum, frame):
        logging.info("Shutdown signal received. Saving state...")
        self._save_processed_articles()
        logging.info("Clean shutdown complete.")
        exit(0)

    def _load_processed_articles(self):
        try:
            with open(self.config["processed_articles_file"], "r") as f:
                self.processed_articles = {line.strip() for line in f if line.strip()}
                logging.info(f"Loaded {len(self.processed_articles)} processed articles.")
        except FileNotFoundError:
            logging.warning("No processed articles file found. Starting fresh.")

    def _save_processed_articles(self):
        try:
            with open(self.config["processed_articles_file"], "w") as f:
                f.write("\n".join(self.processed_articles))
                logging.debug(f"Saved {len(self.processed_articles)} processed articles.")
        except Exception as e:
            logging.error(f"Failed to save processed articles: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def _fetch_news_for_category(self, category: str) -> list:
        params = {
            "category": category,
            "language": "en",
            "apiKey": os.getenv("NEWSAPI_KEY")
        }
        response = self.session.get("https://newsapi.org/v2/top-headlines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data.get("articles"), list):
            raise ValueError("Invalid NewsAPI response format")
        logging.info(f"Fetched {len(data['articles'])} articles for category '{category}'.")
        return data["articles"]

    def _fetch_news(self) -> list:
        all_articles = []
        for category in self.config["news_categories"]:
            try:
                articles = self._fetch_news_for_category(category)
                all_articles.extend(articles)
            except Exception as e:
                logging.error(f"Failed to fetch news for category '{category}': {e}")
        return all_articles

    def _generate_article_id(self, article: dict) -> str:
        content = f"{article.get('title', '')}{article.get('description', '')}"
        return hashlib.md5(content.encode()).hexdigest()

    def _analyze_article(self, headline: str) -> Optional[Dict]:
        headers = {
            "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": self.config["prompts"]["system_prompt"]},
                {"role": "user", "content": self.config["prompts"]["user_prompt"].format(headline=headline)}
            ],
            "temperature": 0.0,
            "max_tokens": 150
        }
        try:
            response = self.session.post(os.getenv("DEEPSEEK_API_URL"), json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return self._parse_analysis(content)
        except Exception as e:
            logging.error(f"Analysis failed: {e}")
            return None

    def _parse_analysis(self, content: str) -> Dict:
        patterns = {
            "Recommendation": r"Recommendation:\s*(Buy|Sell|Hold)",
            "Confidence": r"Confidence:\s*(Low|Medium|High)",
            "Risk": r"Risk:\s*(Low|Medium|High)",
            "Why": r"Why:\s*(.*?)(?=\s*Ticker:|$)",
            "Ticker": r"Ticker:\s*([A-Z]{1,5})",
            "Sector": r"Sector:\s*(.+?)(?=$)"
        }
        result = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            result[key] = match.group(1).strip() if match else "N/A"
        return result

    def _send_telegram_message(self, message: str):
        url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage"
        payload = {"chat_id": os.getenv("USER_CHAT_ID"), "text": message, "parse_mode": "Markdown"}
        try:
            response = self.session.post(url, data=payload, timeout=10)
            response.raise_for_status()
            logging.info("Telegram message sent successfully.")
        except requests.RequestException as e:
            logging.error(f"Telegram API error: {e}")

    def _format_telegram_message(self, article: dict, analysis: dict) -> str:
        ticker = analysis.get("Ticker", "N/A")
        sector = analysis.get("Sector", "N/A")
        finviz_sector = sector.lower().replace(" ", "")
        try:
            date_obj = datetime.fromisoformat(article.get('publishedAt', '').replace('Z', '+00:00'))
            published_at = date_obj.strftime('%Y-%m-%d %H:%M')
        except:
            published_at = "N/A"

        return (
            f"📰 [{article.get('title', 'N/A')}]({article.get('url', '#')})\n"
            f"Source: [{article.get('source', {}).get('name', 'N/A')}]({article.get('url', '#')}) | 🗓️ {published_at}\n\n"
            f"*🔍 Analysis*\n"
            f"Recommendation: **{analysis.get('Recommendation', 'N/A')}**\n"
            f"Confidence: {analysis.get('Confidence', 'N/A')} | Risk: {analysis.get('Risk', 'N/A')}\n"
            f"Rationale: {analysis.get('Why', 'N/A')}\n\n"
            f"Ticker: `${ticker}` | Sector: [{sector}](https://finviz.com/screener.ashx?f=sec_{finviz_sector}&v=211)\n"
            f"[Yahoo Finance](https://finance.yahoo.com/quote/{ticker}) | [Finviz](https://finviz.com/quote.ashx?t={ticker}) | [TradingView](https://www.tradingview.com/symbols/{ticker}/)"
        )

    def _process_article(self, article: dict):
        article_id = self._generate_article_id(article)
        if article_id in self.processed_articles:
            return

        headline = article.get("title")
        if not headline:
            return

        analysis = self._analyze_article(headline)
        if analysis and analysis.get("Ticker") != "N/A":
            message = self._format_telegram_message(article, analysis)
            self._send_telegram_message(message)
            self.processed_articles.add(article_id)

    def run(self):
        self._load_processed_articles()
        logging.info("Trading bot started successfully.")
        while True:
            try:
                articles = self._fetch_news()
                for article in articles:
                    self._process_article(article)
                self._save_processed_articles()
                time.sleep(self.config["fetch_interval_seconds"])
            except Exception as e:
                logging.error(f"Critical error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    config = load_config()
    setup_logging(config["log_file"])
    bot = TradingBot(config)
    bot.run()