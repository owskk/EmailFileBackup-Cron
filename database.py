import os
import logging
import mysql.connector
from mysql.connector import errorcode, pooling
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

# 从环境变量获取数据库连接 URL
DATABASE_URL = os.getenv("DATABASE_URL")

# 全局连接池
connection_pool = None



def get_db_connection():
    """
    使用连接池获取数据库连接,提升性能并避免连接耗尽。
    """
    global connection_pool
    
    if not DATABASE_URL:
        logger.error("❌ 数据库连接失败: DATABASE_URL 环境变量未设置。")
        return None
    
    try:
        # 初始化连接池(仅第一次)
        if connection_pool is None:
            url = urlparse(DATABASE_URL)
            connection_pool = pooling.MySQLConnectionPool(
                pool_name="mailbridge_pool",
                pool_size=3,  # 减小连接池大小，适合 Vercel 无服务器环境
                pool_reset_session=True,
                autocommit=False,
                connect_timeout=10,  # 连接超时 10 秒
                host=url.hostname,
                port=url.port or 3306,
                user=url.username,
                password=url.password,
                database=url.path[1:]  # 去掉路径开头的 '/'
            )
            logger.info("✅ 数据库连接池初始化成功(pool_size=3)。")
        
        # 从连接池获取连接
        return connection_pool.get_connection()
    except mysql.connector.Error as err:
        logger.error(f"❌ 数据库连接失败: {err}")
        return None


def init_db():
    """
    初始化数据库，如果 'upload_logs' 和 'app_locks' 表不存在，则创建它们。
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # 创建 upload_logs 表
        logs_table_name = "upload_logs"
        create_logs_table_query = f"""
        CREATE TABLE IF NOT EXISTS {logs_table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            filename VARCHAR(255) NOT NULL,
            size_bytes INT NOT NULL,
            status VARCHAR(50) NOT NULL
        ) ENGINE=InnoDB;
        """
        cursor.execute(create_logs_table_query)
        logger.info(f"✅ 数据库表 '{logs_table_name}' 初始化成功。")

        # 创建 app_locks 表
        locks_table_name = "app_locks"
        create_locks_table_query = f"""
        CREATE TABLE IF NOT EXISTS {locks_table_name} (
            lock_name VARCHAR(255) PRIMARY KEY,
            is_locked BOOLEAN NOT NULL DEFAULT FALSE,
            locked_at TIMESTAMP NULL
        ) ENGINE=InnoDB;
        """
        cursor.execute(create_locks_table_query)
        logger.info(f"✅ 数据库表 '{locks_table_name}' 初始化成功。")

        # 创建索引以优化查询性能
        logger.info("正在创建数据库索引...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON upload_logs(timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_filename ON upload_logs(filename)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON upload_logs(status)")
            logger.info("✅ 数据库索引创建成功。")
        except mysql.connector.Error as idx_err:
            # 索引可能已存在,不影响主流程
            logger.warning(f"索引创建警告: {idx_err}")

        conn.commit()

    except mysql.connector.Error as err:
        logger.error(f"❌ 创建数据库表失败: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def release_lock(lock_name: str):
    """
    释放一个命名的锁。
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE app_locks SET is_locked = FALSE, locked_at = NULL WHERE lock_name = %s", (lock_name,))
        conn.commit()
        logger.info(f"✅ 成功释放锁: '{lock_name}'")
    except mysql.connector.Error as err:
        logger.error(f"❌ 释放锁时发生数据库错误: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def cleanup_stale_locks():
    """
    清理所有僵死锁。
    在应用启动时调用，无条件清理所有锁。
    
    因为每次启动都是新的实例（尤其在 Vercel 无服务器环境），
    旧实例的锁都应该被清理，无需检查超时时间。
    """
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        # 无条件清理所有锁
        query = """
            UPDATE app_locks 
            SET is_locked = FALSE, locked_at = NULL 
            WHERE is_locked = TRUE
        """
        cursor.execute(query)
        cleared = cursor.rowcount
        conn.commit()
        
        if cleared > 0:
            logger.warning(f"⚠️ 启动时清理了 {cleared} 个僵死锁")
        else:
            logger.info("✅ 启动时检查：没有发现僵死锁")
            
    except mysql.connector.Error as err:
        logger.error(f"❌ 清理僵死锁失败: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def acquire_lock(lock_name: str, timeout_minutes: int = 30) -> bool:
    """
    尝试获取一个命名的锁。如果锁已被占用但超时，则强制释放后获取。
    
    Args:
        lock_name: 锁的名称
        timeout_minutes: 锁超时时间（分钟），默认30分钟
        
    Returns:
        bool: 成功获取锁返回 True，否则返回 False
    """
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        # 确保锁记录存在
        cursor.execute("INSERT IGNORE INTO app_locks (lock_name) VALUES (%s)", (lock_name,))

        # 尝试以原子方式获取锁
        # FOR UPDATE 会锁定行，直到事务结束
        cursor.execute("START TRANSACTION")
        cursor.execute("""
            SELECT is_locked, locked_at 
            FROM app_locks 
            WHERE lock_name = %s 
            FOR UPDATE
        """, (lock_name,))
        result = cursor.fetchone()

        if result:
            is_locked, locked_at = result
            
            # 如果锁被占用，检查是否超时
            if is_locked:
                if locked_at:
                    # 计算锁占用时长
                    time_diff = datetime.now() - locked_at
                    if time_diff.total_seconds() > timeout_minutes * 60:
                        logger.warning(
                            f"🟡 锁 '{lock_name}' 已超时 ({int(time_diff.total_seconds() / 60)} 分钟)，强制释放"
                        )
                        # 强制释放超时的锁
                        cursor.execute("""
                            UPDATE app_locks 
                            SET is_locked = FALSE, locked_at = NULL 
                            WHERE lock_name = %s
                        """, (lock_name,))
                        is_locked = False
                else:
                    # 没有时间戳的旧锁，强制释放
                    logger.warning(f"🟡 锁 '{lock_name}' 没有时间戳，强制释放")
                    cursor.execute("""
                        UPDATE app_locks 
                        SET is_locked = FALSE, locked_at = NULL 
                        WHERE lock_name = %s
                    """, (lock_name,))
                    is_locked = False
            
            # 尝试获取锁
            if not is_locked:
                cursor.execute("""
                    UPDATE app_locks 
                    SET is_locked = TRUE, locked_at = CURRENT_TIMESTAMP 
                    WHERE lock_name = %s
                """, (lock_name,))
                conn.commit()
                logger.info(f"✅ 成功获取锁: '{lock_name}'")
                return True
            else:
                conn.rollback()
                logger.warning(f"🟡 未能获取锁 '{lock_name}'，因为它已被占用。")
                return False
        else:
            conn.rollback()
            return False

    except mysql.connector.Error as err:
        logger.error(f"❌ 获取锁时发生数据库错误: {err}")
        if conn.is_connected():
            conn.rollback()
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def release_lock(lock_name: str):
    """
    释放一个命名的锁。
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE app_locks SET is_locked = FALSE, locked_at = NULL WHERE lock_name = %s", (lock_name,))
        conn.commit()
        logger.info(f"✅ 成功释放锁: '{lock_name}'")
    except mysql.connector.Error as err:
        logger.error(f"❌ 释放锁时发生数据库错误: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def log_upload(filename: str, size_bytes: int, status: str):
    """
    向数据库中插入一条附件上传记录。
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        insert_query = """
                       INSERT INTO upload_logs (filename, size_bytes, status)
                       VALUES (%s, %s, %s) \
                       """
        cursor.execute(insert_query, (filename, size_bytes, status))
        conn.commit()
        logger.info(f"记录到数据库: {filename} ({size_bytes} bytes) - {status}")
    except mysql.connector.Error as err:
        logger.error(f"❌ 写入数据库失败: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_logs_paginated(page: int = 1, per_page: int = 20, search_query: str = None):
    """
    从数据库中分页获取最新的日志记录，支持搜索。
    """
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        offset = (page - 1) * per_page

        params = []
        where_clause = ""
        if search_query:
            where_clause = "WHERE filename LIKE %s"
            params.append(f"%{search_query}%")

        query = f"SELECT * FROM upload_logs {where_clause} ORDER BY timestamp DESC LIMIT %s OFFSET %s"

        params.extend([per_page, offset])

        cursor.execute(query, tuple(params))
        logs = cursor.fetchall()
        return logs
    except mysql.connector.Error as err:
        logger.error(f"❌ 从数据库读取日志失败: {err}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_total_log_count(search_query: str = None):
    """
    获取日志总数，支持搜索。
    """
    conn = get_db_connection()
    if not conn:
        return 0
    try:
        cursor = conn.cursor()

        params = []
        where_clause = ""
        if search_query:
            where_clause = "WHERE filename LIKE %s"
            params.append(f"%{search_query}%")

        query = f"SELECT COUNT(*) FROM upload_logs {where_clause}"
        cursor.execute(query, tuple(params))
        count = cursor.fetchone()[0]
        return count
    except mysql.connector.Error as err:
        logger.error(f"❌ 从数据库读取日志数失败: {err}")
        return 0
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_log_count_by_status(status: str) -> int:
    """
    获取指定状态的日志数量,用于统计展示。
    """
    conn = get_db_connection()
    if not conn:
        return 0
    try:
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM upload_logs WHERE status = %s"
        cursor.execute(query, (status,))
        count = cursor.fetchone()[0]
        return count
    except mysql.connector.Error as err:
        logger.error(f"❌ 从数据库读取状态统计失败: {err}")
        return 0
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# 在模块加载时自动初始化数据库
# 初始化逻辑移至 app.py 中显式调用

