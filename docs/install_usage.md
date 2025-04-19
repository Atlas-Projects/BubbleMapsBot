# 🚀 Installation & Usage Guide

This document provides step-by-step instructions to install, configure, and run the project.

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone git@github.com:Atlas-Projects/BubbleMapsBot.git
cd BubbleMapsBot
```

### 2. Create a Virtual Environment (Optional but Recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium --with-deps --only-shell
```

Make sure your Python version is **3.8+**.

---

## ⚙️ Configuration

1. Copy the sample config file: `cp sample_config.yaml config.yaml`

2. Open `config.yaml` and fill in all required values. Refer to the [Configuration File Documentation](./config_vars.md) for help.

---

## 🧪 Running the Bot

### Option 1: Long Polling Mode (default)

```bash
python3 -OO -m bubblemaps_bot   # On Windows: python -OO -m bubblemaps_bot
```

Make sure the `webhook` option in your config is set to `false`.

---

### Option 2: Webhook Mode

1. Ensure your server is accessible via HTTPS and your `webhook_url`, `webhook_port`, and `webhook_cert_path` are correctly set in the config.

2. Start the application:

```bash
python3 -OO -m bubblemaps_bot   # On Windows: python -OO -m bubblemaps_bot
```

---

## 🛠 Developer Notes

- Ensure your Redis/Valkey server is running if enabled in config.
- While we only include aiosqlite in our requirements, our ORM vendor SQLAlchemy fully supports MySQL, PostgreSQL. The full list of supported databases can be found [here](https://docs.sqlalchemy.org/en/latest/dialects/)
- Use tools like `ngrok` for local webhook testing:

  ```bash
  ngrok http 443
  ```
