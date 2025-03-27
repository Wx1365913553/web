"""增强日志输出和事务管理的数据库导入脚本"""
import os
import re
import logging
import pandas as pd
from sqlalchemy import create_engine, exc, text
from typing import Dict, Optional

# 配置更详细的日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('importer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseImporter:
    def __init__(self, db_config: Dict, table_prefix: str = "data_"):
        self.db_config = db_config
        self.table_prefix = table_prefix
        self.engine = self._create_engine()
        self.varchar_length = 255  
        self.max_varchar_length = 16383 
        self.type_infer_conf = {
            'int_sample_size': 100,  # 整数验证采样数量
            'int_error_rate': 0.05
        }
        # 增强类型推断规则
        self.type_rules = {
            'id': 'BIGINT',
            'date': 'DATE',
            'time': 'TIME',
            'price': 'DECIMAL(12,4)',
            'num': 'INT',
            'cost': 'DECIMAL(12,4)',  # 允许5%的错误率
            'hospital_id': 'VARCHAR(20)',
            'prescription': 'VARCHAR(255)',  # 新增规则
            'bmi_convered_amount': 'VARCHAR(255)',  # 新增规则
            'p_type_pct': 'VARCHAR(255)',  # 新增规则
            'refund_flag_type':'VARCHAR(255)',
            'unit_price':'VARCHAR(255)',
            'self_pay_limit':'VARCHAR(255)',
            'p_type':'VARCHAR(255)'
        }

        # 支持更多日期格式
        self.date_formats = [
            '%d/%m/%Y %H:%M:%S',   # 日月年格式 
            '%d/%m/%y %H:%M:%S',   # 支持短年份
            '%d-%m-%Y %H:%M:%S',   # 破折号分隔
            '%Y-%m-%d %H:%M:%S',   # 标准格式
            '%Y%m%d%H%M%S',        # 无分隔符格式
            '%Y-%m-%d',            # 仅日期
            '%Y/%m/%d %H:%M:%S'    # 斜杠分隔
        ]

    def _sanitize_name(self, name: str) -> str:
        """清理非法字符生成合规名称"""
        # 增加引号去除和多重保护
        return re.sub(r"[^a-zA-Z0-9_]", "_", str(name).strip('"')).lower()
    def _generate_table_name(self, file_path: str) -> str:
        """生成合规表名"""
        base_name = os.path.basename(file_path)
        raw_name = os.path.splitext(base_name)[0]
        sanitized = self._sanitize_name(raw_name)
        return f"{self.table_prefix}{sanitized[:50]}"  # 限制表名长度

    def _generate_ddl(self, df: pd.DataFrame, table_name: str) -> str:
        """生成建表语句"""
        columns = []
        total_length = 0  # 新增行长度跟踪
        
        for col in df.columns:
            sanitized = self._sanitize_name(col)
            dtype = self._infer_data_type(df[col], col)
            
            # 处理特殊字符导致的无效类型
            if dtype.startswith('VARCHAR'):
                # 适当调整VARCHAR长度
                dtype = f"VARCHAR({self.max_varchar_length})" if self.max_varchar_length < 255 else "VARCHAR(255)"
            elif dtype == 'TIME':
                dtype = 'DATETIME'
            elif not dtype.startswith(('VARCHAR', 'INT', 'BIGINT', 'DOUBLE', 'DATETIME', 'DECIMAL')):
                dtype = f"VARCHAR({self.max_varchar_length})"
            if any(kw in sanitized.lower() for kw in ['date', 'time', 'dt']):
                dtype = 'DATETIME'
                

            columns.append(f"`{sanitized}` {dtype}")

        return f"""CREATE TABLE IF NOT EXISTS `{table_name}` (
            {',\n            '.join(columns)},
            `import_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET={self.db_config['charset']};"""

    

    def _create_engine(self):
        """创建带连接池的数据库引擎"""
        return create_engine(
            f"mysql+pymysql://{self.db_config['user']}:{self.db_config['password']}"
            f"@{self.db_config['host']}:{self.db_config.get('port',3306)}"
            f"/{self.db_config['db']}?charset={self.db_config['charset']}",
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # 自动检测连接有效性
            pool_recycle=3600
        )
    def _parse_datetime(self, series: pd.Series) -> Optional[str]:
        """多格式尝试日期解析"""
        # 新增预处理：统一替换日期分隔符
        normalized = series.astype(str).str.replace(r'[/-]', '-', regex=True)
        for fmt in self.date_formats:
            try:
                parsed = pd.to_datetime(
                    normalized,  # 使用预处理后的 normalized 变量
                    format=fmt,
                    errors='coerce',
                    exact=True
                )
                if parsed.notna().any():
                    logger.debug(f"成功匹配日期格式: {fmt}")
                    return "DATETIME"
            except Exception as e:
                logger.debug(f"日期格式尝试失败 {fmt}: {str(e)}")
        return None


    def _infer_data_type(self, series: pd.Series, col_name: str) -> str:
        """智能类型推断逻辑"""
        lower_name = col_name.lower()
        
       
        # 加强数据内容验证
        # 修改类型推断逻辑（_infer_data_type方法中）：
        def is_valid_integer(s):
            cleaned = str(s).strip('"').replace(',', '').replace('_', '').strip()
        # 增加正则匹配确保纯数字
            if not re.match(r'^[-+]?\d+$', cleaned):
                return False
            try:
                int(cleaned)
                return True
            except:
                return False

        # 数值类型检测增强
        if any(kw in lower_name for kw in ['id', 'num', 'code']):
            # 增加采样比例并添加容错
            sample_size = min(200, len(series))  # 扩大采样量
            sample_check = series.sample(sample_size)
            
            if sample_check.apply(is_valid_integer).mean() > 0.95:  # 允许5%容错
                try:
                    # 尝试实际转换验证
                    _ = pd.to_numeric(series, errors='raise')
                    max_val = series.astype(int).max()
                    return "BIGINT" if max_val > 2147483647 else "INT"
                except:
                    pass  # 转换失败时回退到字符串
            return f"VARCHAR({self.max_varchar_length})"  # 明确返回字符串类型
            # 增加对 prescription 列的特殊规则
        # 优先匹配类型规则
        for key in self.type_rules:
            if key in lower_name:
                logger.debug(f"字段 {col_name} 匹配类型规则: {key}")
                return self.type_rules[key]

        # 数值类型检测
        try:
            numeric_series = pd.to_numeric(series, errors='raise')
            if numeric_series.apply(float.is_integer).all():
                max_val = numeric_series.max()
                if max_val > 2147483647:
                    return "BIGINT"
                return "INT"
            return "DOUBLE"
        except Exception as e:
            logger.debug(f"字段 {col_name} 非数值类型: {str(e)}")

        # 日期类型检测
        if (dt_type := self._parse_datetime(series)) is not None:
            return dt_type

        # 字符串类型动态计算长度
        max_len = series.astype(str).str.len().max()
        if max_len >= 16383:
            return "TEXT"
        safe_len = min(int(max_len * 1.2), 5000)  # 降低上限
        if safe_len > 1000:
            return "TEXT"
        final_len = max(45, safe_len)
        logger.debug(f"字段 {col_name} 推断为 VARCHAR({final_len})")
        return f"VARCHAR({max(45, safe_len)})"

    def import_file(self, file_path: str, batch_size: int = 500) -> Dict:
        """强化事务管理和错误处理的主方法"""
        report = {
            'status': 'success',
            'table': '',
            'rows_imported': 0,
            'warnings': []
        }


        try:
            # 检查文件有效性
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
                
            logger.info(f"开始处理文件: {file_path}")
            
            # 使用独立连接会话
            with self.engine.connect() as conn:
                # 显式事务管理
                trans = conn.begin()
                
                try:
                    # 1. 读取数据
                    logger.info("开始读取CSV文件...")
                    df = pd.read_csv(
                        file_path,
                        dtype=str,
                        keep_default_na=False,
                        encoding='utf-8-sig',
                        on_bad_lines='warn',
                        quoting=3,
                        quotechar='"',
                        converters={col_name: lambda x: x.strip('"') for col_name in pd.read_csv(file_path, nrows=0).columns}
                    )
                    # 添加全局引号处理
                    logger.debug("正在清理字段引号...")
                    df = df.apply(lambda col: col.str.strip('"') if col.dtype == object else col)
                    for col in df.columns:
                        sanitized = self._sanitize_name(col)
                        if sanitized == 'unit_price' or sanitized == 'cost':
                            # 将空字符串或无效值替换为 None
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    # 新增列名清洗
                    df.columns = [re.sub(r'\W+', '_', col.strip('"')).lower() for col in df.columns]
                    datetime_columns = [
                        col for col in df.columns 
                        if any(kw in col.lower() for kw in ['date', 'time', 'dt'])
                    ]

                    for col in datetime_columns:
                        df[col] = pd.to_datetime(
                            df[col],
                            format='mixed' if df[col].dtype == object else None,
                            errors='coerce'
                        ).dt.strftime('%Y-%m-%d %H:%M:%S')
                    # 2. 生成表结构
                    table_name = self._generate_table_name(file_path)
                    report['table'] = table_name
                    ddl = self._generate_ddl(df, table_name)
                    
                    # 3. 执行DDL
                    logger.info(f"正在创建表 {table_name}...")
                    conn.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
                    conn.execute(text(ddl))
                    logger.debug(f"执行DDL:\n{ddl}")

                    # 4. 分块导入
                    logger.info("开始数据导入...")
                    total_rows = len(df)
                    for i in range(0, total_rows, batch_size):
                        batch = df.iloc[i:i+batch_size]
                        try:
                            batch.to_sql(
                                name=table_name,
                                con=conn,
                                if_exists='append',
                                index=False,
                                method='multi',
                                chunksize=100
                            )
                            report['rows_imported'] += len(batch)
                            logger.info(f"已提交 {min(i+batch_size, total_rows)}/{total_rows} 行")
                        except Exception as batch_error:
                            logger.error(f"批处理错误: {str(batch_error)}")
                            raise

                    # 提交事务
                    trans.commit()
                    logger.info(f"成功导入 {report['rows_imported']} 行数据到表 {table_name}")

                except Exception as e:
                    # 回滚事务并记录错误
                    logger.error(f"操作失败: {str(e)}")
                    trans.rollback()
                    raise

        except pd.errors.ParserError as e:
            error_msg = f"CSV解析失败: {str(e)}"
            logger.error(error_msg)
            report.update({'status': 'error', 'message': error_msg})
        except exc.SQLAlchemyError as e:
            error_msg = f"数据库错误({e.orig.args[0]}): {e.orig.args[1]}"
            logger.error(error_msg)
            report.update({'status': 'error', 'message': error_msg})
        except Exception as e:
            error_msg = f"系统错误: {str(e)}"
            logger.error(error_msg)
            report.update({'status': 'error', 'message': error_msg})

        return report

    # 其他辅助方法保持不变...

if __name__ == "__main__":

    importer = DatabaseImporter()
    result = importer.import_file(
        file_path=r"D:\Administrator\Desktop\圣莱地\山南藏医院\MZMX.csv",
        batch_size=5000
    )

    # 添加结果输出
    print("\n" + "="*50)
    print("导入结果摘要:")
    print(f"状态: {result['status'].upper()}")
    print(f"表名: {result.get('table', 'N/A')}")
    # print(f"导入行数: {result.get('rows_imported', 0)}")
    if result['status'] == 'error':
        print(f"错误信息: {result.get('message', '未知错误')}")
    print("="*50)
