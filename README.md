# Discord Forum Search Assistant

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Discord.py](https://img.shields.io/badge/Discord.py-2.3+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**Discord Forum Search Assistant** is a high-performance bot designed to overcome the limitations of Discord's native Forum Channel search. It provides advanced filtering, Boolean logic search, result caching, and an interactive paginated interface.

## ✨ Key Features

- **🔍 Advanced Search**: Supports `AND`, `OR`, `NOT` logic, and exact phrase matching.
- **⚡ High Performance**: Built-in dual-layer caching (Redis + Memory) and embedded SQLite database for instant results.
- **🎛 Multi-dimensional Filtering**: Filter by tags, author, date range, reaction count, and reply count.
- **📊 Interactive UI**: Paginated results (5 per page) with navigation buttons and history support.
- **💾 Data Persistence**: Uses SQLite for automatic indexing without needing external database servers.

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.11+
- Discord Bot Token ([Get it here](https://discord.com/developers/applications))
- (Optional) Docker

### Method 1: Local Execution

1.  **Clone the repository**

    ```bash
    git clone https://github.com/yourusername/discord-forum-search-assistant.git
    cd discord-forum-search-assistant
    ```

2.  **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    Copy the example config and add your token:

    ```bash
    cp .env.example .env
    # Open .env and set DISCORD_TOKEN=your_token_here
    ```

4.  **Run the bot**
    ```bash
    python main.py
    ```

### Method 2: Docker Deployment (Recommended)

Use Docker Compose to start the bot (includes Redis support):

```yaml
# docker-compose.yml example
version: "3.8"
services:
  bot:
    image: python:3.11-slim
    volumes:
      - .:/app
    command: python main.py
    environment:
      - DISCORD_TOKEN=your_token_here
      - USE_DATABASE_INDEX=true
```

Start the service:

```bash
docker-compose up -d
```

---

## 📖 Usage Guide

### Basic Command

Type `/forum_search` in any channel to open the search panel.

### Parameter Reference

| Parameter         | Description                                       | Example                            |
| :---------------- | :------------------------------------------------ | :--------------------------------- |
| `forum_name`      | **(Required)** Select the forum channel to search | (Auto-complete selection)          |
| `search_word`     | Keywords (supports logic)                         | `python AND tutorial`              |
| `exclude_word`    | Exclude posts containing these words              | `outdated`                         |
| `tag1` - `tag3`   | Filter by specific tags                           | `Official`                         |
| `original_poster` | Filter by author                                  | `@User`                            |
| `min_reactions`   | Minimum reaction count                            | `10`                               |
| `start_date`      | Start date (supports relative time)               | `2024-01-01` or `7d` (last 7 days) |
| `order`           | Sort order                                        | `Most Reactions` / `Newest`        |

### 🔎 Advanced Search Syntax

You can use the following syntax inside the `search_word` parameter:

- **AND**: `python discord` or `python AND discord`
- **OR**: `bug OR issue`
- **NOT**: `NOT deprecated`
- **Exact Phrase**: `"error 404"` (use double quotes)
- **Grouping**: `(tutorial OR guide) AND python`

### 💡 Practical Examples

**1. Find trending discussions from the last week:**

```bash
/forum_search forum_name:General start_date:7d min_reactions:10 order:Most Reactions Descending
```

**2. Find specific tutorials, excluding outdated content:**

```bash
/forum_search forum_name:Tech-Share tag1:Tutorial exclude_word:deprecated
```

**3. Find bug reports from a specific user:**

```bash
/forum_search forum_name:Bug-Reports original_poster:@Username tag1:Pending
```

---

## ⚙️ Environment Variables (.env)

| Variable             | Default                | Description                                           |
| :------------------- | :--------------------- | :---------------------------------------------------- |
| `DISCORD_TOKEN`      | (None)                 | **Required**. Your bot token                          |
| `USE_DATABASE_INDEX` | `true`                 | Enable SQLite indexing for speed                      |
| `DB_PATH`            | `data/searchdb.sqlite` | Path to the SQLite database                           |
| `REDIS_URL`          | (Empty)                | Redis connection URL (Optional, Recommended for Prod) |
| `LOG_LEVEL`          | `INFO`                 | Logging level (DEBUG/INFO/WARNING)                    |

## ❓ FAQ

**Q: The bot returns no results?**
A: Ensure the bot has `View Channel` and `Read Message History` permissions in the target Forum channel.

**Q: Why do I only see some results?**
A: To maintain performance, search results are capped at 1000 items per query. Use date ranges or tags to narrow your search.

**Q: Where is the database stored?**
A: By default at `data/searchdb.sqlite`. If using Docker, ensure you mount the `/data` volume to persist the index.

## 📄 License

This project is open source under the [MIT License](LICENSE).
