<div align="center">
  <h1>Telegram Bubblemap Bot</h1>
</div>

A powerful Telegram bot that integrates with the [BubbleMaps](https://app.bubblemaps.io/) API to deliver token insights, distribution analytics, and interactive bubblemaps — all directly within Telegram.

---

## ✨ Features

- 🔍 **Check token details** for any supported token address
- 🫧 **Generate bubblemaps** for supported tokens across multiple chains
- 📊 **Inline token distribution breakdowns** with visual data
- 🧾 **Fetch holder/address-specific insights** for a token
- 📈 **CoinGecko integration** for market data and metadata
- 📦 **Redis-compatible Valkey caching** for performance and response optimization
- 🌐 **Webhook or polling support** for Telegram integration
- 🔗 **Multi-chain support** including: `eth`, `bsc`, `ftm`, `avax`, `cro`, `arbi`, `poly`, `base`, `sol`, and `sonic`

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone git@github.com:Atlas-Projects/BubbleMapsBot.git
cd BubbleMapsBot/
```

### 2. Create a Virtual Environment (Optional)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

1. Copy the sample config:

```bash
cp sample_config.yaml config.yaml
```

2. Edit `config.yaml` to include your Telegram Bot Token, supported features, and API details.

Refer to the [Configuration File Documentation](./docs/config_vars.md) for a complete explanation of each parameter.

---

## 🚀 Usage

### Run in Polling Mode (default)

```bash
python3 -OO -m bubblemaps_bot   # On Windows: python -OO -m bubblemaps_bot
```

Ensure `webhook: false` in your `config.yaml`.

### Run in Webhook Mode

Ensure you have:

- A public HTTPS server
- Proper `webhook_url`, `webhook_port`, and SSL cert path set

Then:

```bash
python3 -OO -m bubblemaps_bot   # On Windows: python -OO -m bubblemaps_bot
```

---

## 🧪 Example Commands

Here are some of the capabilities your users can try within Telegram:

- `/check <address>` – View details about a token
- `/mapshot <address>` – Get an interactive Bubblemap
- `/meta <token_address> or /meta <chain> <token_address>` – Get metadata about a specific token
- `/distribution <token>` – Get distribution information about a token
- `/coin <address>` – Price and market data from CoinGecko
- `/address <chain> <token_address> <address>` – Fetch details of a specific address for a token
- `/clear` – Clear the Valkey cache

---

## 🧩 Supported Chains

- Ethereum (`eth`)
- Binance Smart Chain (`bsc`)
- Fantom (`ftm`)
- Avalanche (`avax`)
- Cronos (`cro`)
- Arbitrum (`arbi`)
- Polygon (`poly`)
- Base (`base`)
- Solana (`sol`)
- Sonic (`sonic`)

---

## 🔄 Updating

To update the project:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## 🐍 Python Dependencies

This project uses the following core Python packages:

| Package | Description |
|--------|-------------|
| [`python-telegram-bot`](https://pypi.org/project/python-telegram-bot/) | Official Telegram Bot API framework – used to handle messaging, commands, and updates. |
| [`SQLAlchemy`](https://pypi.org/project/SQLAlchemy/) | Python SQL toolkit and ORM used for database interactions. |
| [`aiohttp`](https://pypi.org/project/aiohttp/) | Asynchronous HTTP client/server for non-blocking requests, ideal for webhook mode and API calls. |
| [`aiosqlite`](https://pypi.org/project/aiosqlite/) | Async interface to SQLite – useful for lightweight, non-blocking storage. |
| [`PyYAML`](https://pypi.org/project/PyYAML/) | Used for reading and parsing the `config.yaml` configuration file. |
| [`valkey`](https://pypi.org/project/valkey/) | Valkey/Redis-compatible client for high-performance in-memory caching and key-value store access. |
| [`setuptools`](https://pypi.org/project/setuptools/) | Helps with packaging and distributing the application, required by some dependencies. |
| [`playwright`](https://pypi.org/project/playwright/) | Headless browser automation – used for capturing screenshots or rendering visual elements (if needed). |

> Full list can be found in [`requirements.txt`](./requirements.txt)

---

## 📜 License

MIT License. See [LICENSE](./LICENSE) for full details.
