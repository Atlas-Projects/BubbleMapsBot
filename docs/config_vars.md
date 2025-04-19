# 🛠 Configuration File Documentation

This guide explains each parameter in the `config.yaml` file, helping you understand what values to provide and how they affect the application.

---

## 📩 Telegram Configuration

| Parameter            | Type      | Description |
|----------------------|-----------|-------------|
| `bot_token`          | `string`  | Telegram bot API token. Obtain it from [BotFather](https://t.me/botfather). |
| `drop_updates`       | `boolean` | Whether to drop any pending updates on bot startup (`true` or `false`). Useful for avoiding spam. |
| `webhook`            | `boolean` | Whether to use Telegram webhooks (`true`) or long polling (`false`). |
| `webhook_url`        | `string`  | Public HTTPS URL for receiving Telegram updates when `webhook` is enabled. |
| `webhook_port`       | `int`     | Port your server listens on for webhook updates. Commonly `443`, `8443`, etc. |
| `webhook_cert_path`  | `string`  | Absolute path to the SSL certificate file required for Telegram webhooks. |
| `sudo_users`         | `list[int]` | List of Telegram user IDs who are allowed to access admin commands. |

---

## 🗄 Database Configuration

| Parameter  | Type     | Description |
|------------|----------|-------------|
| `schema`   | `string` | Database schema name. Depending on your DB setup, this might be `public` or a custom name. |

---

## ⚙️ Valkey (Redis-compatible DB) Configuration

| Parameter           | Type       | Description |
|---------------------|------------|-------------|
| `enabled`           | `boolean`  | Enable or disable Valkey support (`true` or `false`). |
| `host`              | `string`   | Hostname or IP address of the Valkey/Redis server. E.g., `localhost` or `127.0.0.1`. |
| `port`              | `int`      | Port number Valkey is listening on (default: `6379`). |
| `db`                | `int`      | Redis DB index to use (0-based). |
| `ttl`               | `int`      | Default Time-To-Live (TTL) in seconds for cached items. |
| `screenshot_cache`  | `boolean`  | Whether to cache screenshots in Valkey for performance gains. |

---

## 🫧 Bubblemaps Configuration

### Supported Chains

| Parameter              | Type       | Description |
|------------------------|------------|-------------|
| `supported_chains`     | `list[str]`| List of blockchain identifiers supported for Bubblemap generation. Supported values include: `eth`, `bsc`, `ftm`, `avax`, `cro`, `arbi`, `poly`, `base`, `sol`, `sonic` |

### API Endpoints

| Parameter                 | Type     | Description |
|---------------------------|----------|-------------|
| `base_api_url`            | `string` | Root API endpoint for Bubblemap data. |
| `map_availability_url`   | `string` | URL to check if a bubblemap exists for a given token. |
| `map_metadata_url`       | `string` | URL template to fetch metadata for a token's map. Replace `{chain}` and `{token}` with actual values. |
| `iframe_template_url`    | `string` | Template for embedding a Bubblemap in an iframe. Replace `{chain}` and `{token}` with actual values. |

---

## 📝 Example Usage

```yaml
telegram:
  bot_token: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
  drop_updates: true
  webhook: true
  webhook_url: "https://example.com/bot"
  webhook_port: 443
  webhook_cert_path: "/etc/ssl/certs/bot.pem"
  sudo_users:
    - 123456789
    - 987654321

database:
  schema: "sqlite+aiosqlite:///bubblemaps.db"

valkey:
  enabled: true
  host: "localhost"
  port: 6379
  db: 0
  ttl: 3600
  screenshot_cache: true

bubblemaps:
  supported_chains:
    - eth
    - bsc
    - ftm
    - avax
    - cro
    - arbi
    - poly
    - base
    - sol
    - sonic
  api:
    base_api_url: "https://api-legacy.bubblemaps.io/map-data"
    map_availability_url: "https://api-legacy.bubblemaps.io/map-availability"
    map_metadata_url: "https://api-legacy.bubblemaps.io/map-metadata?chain={chain}&token={token}"
    iframe_template_url: "https://app.bubblemaps.io/{chain}/token/{token}"
```
