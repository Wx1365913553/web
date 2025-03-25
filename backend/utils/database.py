import pymysql
from contextlib import contextmanager

class DBConnection:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'wx123456',
            'db': 'snzyy',
            'charset': 'utf8mb4'
        }
    
    @contextmanager
    def __call__(self):
        conn = pymysql.connect(**self.config)
        try:
            yield conn
        finally:
            conn.close()
    
      # 进入上下文时调用，返回需管理的资源（如连接或游标）
    def __enter__(self):
        self.connection = self._create_connection()  # 创建连接
        return self.connection  # 返回连接对象或自身
    
    # 退出上下文时调用，关闭资源并处理异常
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()
        # 若需抑制异常，可返回 True
    def _create_connection(self):
        # 实际创建数据库连接的逻辑（如 psycopg2/sqlite3 等）
        return pymysql.connect(**self.config)