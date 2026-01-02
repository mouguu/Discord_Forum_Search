"""
数据库管理器 - SQLite连接池和查询优化
仅在config中USE_DATABASE_INDEX=True时启用
"""
import sqlite3
import aiosqlite
import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime
import threading
from contextlib import asynccontextmanager
from config.settings import settings

logger = logging.getLogger('discord_bot.database')

class DatabaseManager:
    """数据库管理器，提供连接池和查询优化"""
    
    def __init__(self, db_path: str, pool_size: int = 5) -> None:
        self.db_path: str = db_path
        self.pool_size: int = pool_size
        self._pool: List[aiosqlite.Connection] = []
        self._pool_lock: asyncio.Lock = asyncio.Lock()
        self._initialized: bool = False
        self._logger: logging.Logger = logger
        
    async def initialize(self) -> None:
        """初始化数据库连接池"""
        if self._initialized:
            return
            
        try:
            # 创建连接池
            for _ in range(self.pool_size):
                conn = await aiosqlite.connect(self.db_path)
                # 启用WAL模式以提高并发性能
                await conn.execute("PRAGMA journal_mode=WAL")
                # 设置同步模式为NORMAL以平衡性能和安全性
                await conn.execute("PRAGMA synchronous=NORMAL")
                # 增加缓存大小
                await conn.execute("PRAGMA cache_size=10000")
                # 启用外键约束
                await conn.execute("PRAGMA foreign_keys=ON")
                self._pool.append(conn)
            
            # 创建表结构
            await self._create_tables()
            
            self._initialized = True
            self._logger.info(f"数据库连接池初始化完成，连接数: {self.pool_size}")
            
        except Exception as e:
            self._logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def _create_tables(self) -> None:
        """创建数据库表结构"""
        async with self.get_connection() as conn:
            # 线程统计表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS thread_stats (
                    thread_id INTEGER PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    reaction_count INTEGER DEFAULT 0,
                    reply_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_guild_id (guild_id),
                    INDEX idx_channel_id (channel_id),
                    INDEX idx_updated_at (updated_at)
                )
            """)
            
            # 搜索历史表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    query TEXT NOT NULL,
                    results_count INTEGER DEFAULT 0,
                    search_time REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_guild_id (guild_id),
                    INDEX idx_created_at (created_at)
                )
            """)
            
            # 性能指标表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    guild_id INTEGER,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_metric_type (metric_type),
                    INDEX idx_guild_id (guild_id),
                    INDEX idx_recorded_at (recorded_at)
                )
            """)
            
            await conn.commit()
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接的上下文管理器"""
        if not self._initialized:
            await self.initialize()
            
        async with self._pool_lock:
            if not self._pool:
                # 如果池为空，创建新连接
                conn = await aiosqlite.connect(self.db_path)
                await conn.execute("PRAGMA journal_mode=WAL")
                await conn.execute("PRAGMA synchronous=NORMAL")
                await conn.execute("PRAGMA cache_size=10000")
                await conn.execute("PRAGMA foreign_keys=ON")
            else:
                conn = self._pool.pop()
        
        try:
            yield conn
        finally:
            async with self._pool_lock:
                if len(self._pool) < self.pool_size:
                    self._pool.append(conn)
                else:
                    await conn.close()
    
    async def upsert_thread_stats(self, thread_id: int, guild_id: int, 
                                 channel_id: int, reaction_count: int, 
                                 reply_count: int) -> None:
        """插入或更新线程统计信息"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT OR REPLACE INTO thread_stats 
                (thread_id, guild_id, channel_id, reaction_count, reply_count, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (thread_id, guild_id, channel_id, reaction_count, reply_count))
            await conn.commit()
    
    async def get_thread_stats(self, thread_id: int) -> Optional[Dict[str, Any]]:
        """获取线程统计信息"""
        async with self.get_connection() as conn:
            async with conn.execute("""
                SELECT reaction_count, reply_count, updated_at
                FROM thread_stats 
                WHERE thread_id = ?
            """, (thread_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'reaction_count': row[0],
                        'reply_count': row[1],
                        'updated_at': row[2]
                    }
                return None
    
    async def get_guild_thread_stats(self, guild_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """获取服务器的线程统计信息"""
        async with self.get_connection() as conn:
            async with conn.execute("""
                SELECT thread_id, channel_id, reaction_count, reply_count, updated_at
                FROM thread_stats 
                WHERE guild_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
            """, (guild_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        'thread_id': row[0],
                        'channel_id': row[1],
                        'reaction_count': row[2],
                        'reply_count': row[3],
                        'updated_at': row[4]
                    }
                    for row in rows
                ]
    
    async def record_search_history(self, user_id: int, guild_id: int, 
                                   query: str, results_count: int, 
                                   search_time: float) -> None:
        """记录搜索历史"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO search_history 
                (user_id, guild_id, query, results_count, search_time)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, guild_id, query, results_count, search_time))
            await conn.commit()
    
    async def get_user_search_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户搜索历史"""
        async with self.get_connection() as conn:
            async with conn.execute("""
                SELECT query, results_count, search_time, created_at
                FROM search_history 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        'query': row[0],
                        'results_count': row[1],
                        'search_time': row[2],
                        'created_at': row[3]
                    }
                    for row in rows
                ]
    
    async def record_performance_metric(self, metric_type: str, metric_value: float, 
                                       guild_id: Optional[int] = None) -> None:
        """记录性能指标"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO performance_metrics 
                (metric_type, metric_value, guild_id)
                VALUES (?, ?, ?)
            """, (metric_type, metric_value, guild_id))
            await conn.commit()
    
    async def get_performance_metrics(self, metric_type: str, 
                                     hours: int = 24) -> List[Tuple[float, str]]:
        """获取性能指标"""
        async with self.get_connection() as conn:
            async with conn.execute("""
                SELECT metric_value, recorded_at
                FROM performance_metrics 
                WHERE metric_type = ? 
                AND recorded_at > datetime('now', '-{} hours')
                ORDER BY recorded_at DESC
            """.format(hours), (metric_type,)) as cursor:
                return await cursor.fetchall()
    
    async def cleanup_old_data(self, days: int = 30) -> None:
        """清理旧数据"""
        async with self.get_connection() as conn:
            # 清理旧的搜索历史
            await conn.execute("""
                DELETE FROM search_history 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            
            # 清理旧的性能指标
            await conn.execute("""
                DELETE FROM performance_metrics 
                WHERE recorded_at < datetime('now', '-{} days')
            """.format(days))
            
            await conn.commit()
            self._logger.info(f"清理了{days}天前的旧数据")
    
    async def close(self) -> None:
        """关闭所有数据库连接"""
        async with self._pool_lock:
            for conn in self._pool:
                await conn.close()
            self._pool.clear()
        self._initialized = False
        self._logger.info("数据库连接池已关闭")

# 全局数据库管理器实例
database_manager: Optional[DatabaseManager] = None

def get_database_manager() -> Optional[DatabaseManager]:
    """获取数据库管理器实例"""
    global database_manager
    
    # 只有在启用数据库索引时才初始化
    if not hasattr(settings, 'database') or not getattr(settings.database, 'use_database_index', False):
        return None
    
    if database_manager is None:
        db_path = getattr(settings.database, 'db_path', 'data/searchdb.sqlite')
        pool_size = getattr(settings.database, 'connection_pool_size', 5)
        database_manager = DatabaseManager(db_path, pool_size)
    
    return database_manager
