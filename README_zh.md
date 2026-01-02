# Discord 论坛搜索助手

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Discord.py](https://img.shields.io/badge/Discord.py-2.3+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**Discord 论坛搜索助手** 是一个高性能的 Discord 机器人，专为解决 Discord 论坛频道（Forum Channels）原生搜索功能不足的问题。它提供高级过滤、布尔逻辑搜索、结果缓存和交互式分页界面。

## ✨ 核心功能

- **🔍 高级搜索**: 支持 `AND`、`OR`、`NOT` 逻辑及精确短语匹配。
- **⚡ 高性能**: 内置 Redis + 内存双层缓存，配合嵌入式 SQLite 数据库，响应速度极快。
- **🎛 多维过滤**: 可按标签、作者、日期范围、反应数（点赞）和回复数筛选。
- **📊 交互体验**: 搜索结果分页显示（每页 5 条），支持翻页、跳转和历史记录查看。
- **💾 数据持久化**: 使用 SQLite 自动保存索引，无需配置外部数据库服务器。

## 🛠️ 安装与配置

### 前置要求

- Python 3.11+
- Discord 机器人 Token ([获取地址](https://discord.com/developers/applications))
- (可选) Docker

### 方法一：本地运行

1.  **克隆仓库**

    ```bash
    git clone https://github.com/yourusername/discord-forum-search-assistant.git
    cd discord-forum-search-assistant
    ```

2.  **安装依赖**

    ```bash
    pip install -r requirements.txt
    ```

3.  **配置环境变量**
    复制配置文件并填入 Token：

    ```bash
    cp .env.example .env
    # 打开 .env 文件，设置 DISCORD_TOKEN=你的机器人Token
    ```

4.  **运行**
    ```bash
    python main.py
    ```

### 方法二：Docker 部署 (推荐)

直接使用 Docker Compose 启动（包含 Redis）：

```yaml
# docker-compose.yml 示例
version: "3.8"
services:
  bot:
    image: python:3.11-slim
    volumes:
      - .:/app
    command: python main.py
    environment:
      - DISCORD_TOKEN=你的Token
      - USE_DATABASE_INDEX=true
```

运行命令：

```bash
docker-compose up -d
```

---

## 📖 使用指南

### 基础命令

在任意频道输入 `/forum_search` 即可唤出搜索面板。

### 常用参数说明

| 参数              | 说明                            | 示例                             |
| :---------------- | :------------------------------ | :------------------------------- |
| `forum_name`      | **(必选)** 选择要搜索的论坛频道 | (自动补全选择)                   |
| `search_word`     | 关键词 (支持逻辑运算)           | `python AND 教程`                |
| `exclude_word`    | 排除包含此关键词的帖子          | `过时`                           |
| `tag1` - `tag3`   | 包含特定标签                    | `官方公告`                       |
| `original_poster` | 按发帖人筛选                    | `@User`                          |
| `min_reactions`   | 最小反应数 (点赞数)             | `10`                             |
| `start_date`      | 搜索起始日期 (支持相对时间)     | `2024-01-01` 或 `7d` (最近 7 天) |
| `order`           | 排序方式                        | `最高反应降序` / `最新发布`      |

### 🔎 高级搜索语法

在 `search_word` 中可以使用以下语法：

- **同时包含 (AND)**: `python discord` 或 `python AND discord`
- **包含其一 (OR)**: `bug OR issue`
- **排除 (NOT)**: `NOT deprecated`
- **精确匹配**: `"error 404"` (使用双引号)
- **组合使用**: `(教程 OR 指南) AND python`

### 💡 实用示例

**1. 查找最近一周的热门讨论：**

```bash
/forum_search forum_name:综合讨论 start_date:7d min_reactions:10 order:最高反应降序
```

**2. 查找特定标签的教程，排除过时内容：**

```bash
/forum_search forum_name:技术分享 tag1:教程 exclude_word:已失效
```

**3. 查找特定用户的 Bug 反馈：**

```bash
/forum_search forum_name:Bug反馈 original_poster:@用户名 tag1:待处理
```

---

## ⚙️ 环境变量配置 (.env)

| 变量名               | 默认值                 | 说明                                |
| :------------------- | :--------------------- | :---------------------------------- |
| `DISCORD_TOKEN`      | (无)                   | **必需**。机器人的 Token            |
| `USE_DATABASE_INDEX` | `true`                 | 是否启用 SQLite 索引以加速搜索      |
| `DB_PATH`            | `data/searchdb.sqlite` | SQLite 数据库路径                   |
| `REDIS_URL`          | (空)                   | Redis 连接地址 (可选，生产环境推荐) |
| `LOG_LEVEL`          | `INFO`                 | 日志等级 (DEBUG/INFO/WARNING)       |

## ❓ 常见问题

**Q: 搜不到帖子？**
A: 请确保机器人拥有该频道的 `View Channel` (查看频道) 和 `Read Message History` (读取历史消息) 权限。

**Q: 搜索结果只显示一部分？**
A: 为保证性能，单次搜索上限为 1000 条结果。请使用日期或标签缩小搜索范围。

**Q: 数据库文件在哪里？**
A: 默认位于 `data/searchdb.sqlite`。如果您使用 Docker，请确保挂载了 `/data` 目录以持久化保存索引。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。
