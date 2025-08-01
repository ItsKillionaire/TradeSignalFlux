# AI-Powered News Trading Bot

## Project Overview

This project implements an AI-powered news trading bot designed to fetch real-time financial news, analyze it using a large language model (DeepSeek API), and provide actionable trading recommendations via Telegram notifications. The bot is built with a focus on modularity, security, and clear communication of trading signals.

## Features

*   **Real-time News Fetching:** Integrates with NewsAPI to retrieve the latest business, technology, and finance headlines.
*   **AI-Powered Analysis:** Utilizes the DeepSeek API to analyze news sentiment and generate trading recommendations (Buy/Sell/Hold), along with confidence and risk assessments.
*   **Telegram Notifications:** Delivers rich, formatted trading signals directly to your Telegram chat, including embedded links to financial data sites.
*   **Secure Configuration:** Separates sensitive API keys and tokens into a `.env` file, ensuring they are not exposed in version control.
*   **Modular Design:** Organized into `src/` and `config/` directories for improved maintainability and scalability.
*   **Persistent State:** Tracks processed articles to prevent duplicate notifications.
*   **Robust Error Handling:** Implements retry mechanisms for API calls and graceful shutdown procedures.

## Prerequisites

Before running the bot, ensure you have the following installed:

*   **Python 3.8+**
*   **pip** (Python package installer)
*   **Virtual Environment:** Highly recommended for managing project dependencies.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ItsKillionaire/TradeSignalFlux
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv myenv
    source myenv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

All sensitive information and core bot settings are managed through two files: `.env` and `config/config.yaml`.

### `.env` File (Sensitive Information)

Create a file named `.env` in the root directory of the project and populate it with your API keys and Telegram details. **Do NOT commit this file to Git.**

```dotenv
NEWSAPI_KEY="YOUR_NEWSAPI_KEY"
DEEPSEEK_API_KEY="YOUR_DEEPSEEK_API_KEY"
DEEPSEEK_API_URL="https://api.deepseek.com/v1/chat/completions"
BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
USER_CHAT_ID="YOUR_TELEGRAM_CHAT_ID"
```

*   **`NEWSAPI_KEY`**: Obtain this from [NewsAPI](https://newsapi.org/).
*   **`DEEPSEEK_API_KEY`**: Obtain this from [DeepSeek API](https://platform.deepseek.com/).
*   **`DEEPSEEK_API_URL`**: The endpoint for the DeepSeek chat completions API.
*   **`BOT_TOKEN`**: Create a new bot via BotFather on Telegram and get your bot token.
*   **`USER_CHAT_ID`**: Your unique Telegram chat ID. You can get this by sending a message to your bot and then accessing `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`.

### `config/config.yaml` (Bot Settings)

This file contains non-sensitive configuration parameters and AI prompts. You can adjust these to fine-tune the bot's behavior.

```yaml
fetch_interval_seconds: 60
processed_articles_file: "processed_articles.txt"
log_file: "trading_bot.log"
news_categories: ["business", "technology", "finance"]

prompts:
  system_prompt: >
    As a seasoned financial analyst, your task is to analyze the following news headline and provide a comprehensive, actionable trading recommendation.
    Infer the most likely stock ticker and sector. If the sector is not immediately obvious, use your best judgment to assign one.
    The output must be in the following format:
    Recommendation: <Buy/Sell/Hold>
    Confidence: <Low/Medium/High>
    Risk: <Low/Medium/High>
    Why: <A brief, data-driven explanation (max 30 words)>
    Ticker: <The stock ticker (e.g., AAPL, GOOGL)>
    Sector: <The primary sector of the company (e.g., Technology, Healthcare)>

  user_prompt: "Analyze the following news headline: {headline}"
```

*   **`fetch_interval_seconds`**: How often the bot fetches new articles (in seconds).
*   **`processed_articles_file`**: The file used to store IDs of already processed articles.
*   **`log_file`**: The file where bot logs are recorded.
*   **`news_categories`**: A list of NewsAPI categories to fetch news from.
*   **`prompts`**:
    *   **`system_prompt`**: Instructions for the AI's role and expected output format.
    *   **`user_prompt`**: The template for the user's input to the AI.

## Usage

1.  **Navigate to the project root directory.**

2.  **Activate your virtual environment:**
    ```bash
    source myenv/bin/activate
    ```

3.  **Run the bot:**
    ```bash
    python src/main.py
    ```

The bot will now run continuously, fetching news, analyzing it, and sending Telegram notifications. You can stop the bot by pressing `Ctrl+C`.

## Project Structure

```
TradeSignalFlux/
├── .env                  # Stores sensitive API keys and tokens
├── requirements.txt      # Lists all Python dependencies
├── processed_articles.txt# Stores IDs of processed articles to prevent duplicates
├── trading_bot.log       # Log file for bot activity
├── config/
│   └── config.yaml       # Non-sensitive configuration and AI prompts
└── src/
    └── main.py           # Main application logic for the trading bot
```

## Future Enhancements

*   **Multiple AI Models:** Support for different LLMs (e.g., OpenAI, Gemini) for analysis.
*   **Trading Platform Integration:** Connect directly to a trading platform for automated trade execution based on signals.
*   **Sentiment Analysis Refinement:** Implement more advanced NLP techniques for nuanced sentiment analysis.
*   **Backtesting Module:** Allow historical news data to be replayed to test trading strategies.
*   **Web Interface:** A simple dashboard to monitor bot activity and signals.
*   **Dockerization:** Containerize the application for easier deployment.
