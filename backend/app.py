from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import pandas as pd
from pathlib import Path
from utils.AutoDBImporter import DatabaseImporter
from utils.database import DBConnection
from utils.excel import export_to_excel
from math import ceil

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'wx123456',
    'database': 'snzyy',
    'charset': 'utf8mb4'
}

# 配置
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config/sql_config.json"
EXPORT_DIR = BASE_DIR / "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

# 创建 DBConnection 类的实例
db_connection = DBConnection()

# 访问 config 属性
db_config = db_connection.config

# 加载SQL配置
def load_sql_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)  # 直接返回列表
    except:
        return []
# 保存SQL配置
def save_sql_config(configs):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(configs, f, ensure_ascii=False, indent=2)

# 上传CSV并导入数据库
@app.route('/api/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV files allowed'}), 400
    
    try:
        print(f"收到文件: {file.filename}")
        temp_file_path = BASE_DIR / "temp" / file.filename
        os.makedirs(BASE_DIR / "temp", exist_ok=True)
        file.save(temp_file_path)
        print(f"文件保存路径: {temp_file_path}")
        
        if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
            return jsonify({'error': '文件未成功保存'}), 500
        
        importer = DatabaseImporter(db_config)
        report = importer.import_file(file_path=str(temp_file_path))
        
        os.remove(temp_file_path)
        
        return jsonify(report), 200 if report['status'] == 'success' else 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# 获取SQL配置列表
@app.route('/api/sql-configs', methods=['GET'])
def get_sql_configs():
    configs = load_sql_config()
    return jsonify(configs)

# 修改配置添加接口
@app.route('/api/sql-configs', methods=['POST'])
def add_sql_config():
    data = request.json
    configs = load_sql_config()
    
    if any(c['name'] == data['name'] for c in configs):
        return jsonify({'error': '模板已存在'}), 400
    
    if not all(key in data for key in ['name', 'filename_prefix', 'sql_template']):
        return jsonify({'error': '缺少必要字段'}), 400
    configs.append({
        "name": data['name'],
        "filename_prefix": data['filename_prefix'],
        "codes": data.get('codes', []),
        "sql_template": data['sql_template']
    })
    
    save_sql_config(configs)
    return jsonify({
            'success': True,
            'data': configs[-1]  # 包装为标准响应格式
    }), 201 

# 在后端app.py添加删除接口
@app.route('/api/sql-configs/<name>', methods=['DELETE'])
def delete_sql_config(name):
    configs = load_sql_config()
    
    # 查找对应配置项
    index = next((i for i, c in enumerate(configs) if c['name'] == name), -1)
    if index == -1:
        return jsonify({'error': 'Config not found'}), 404
    
    del configs[index]
    save_sql_config(configs)
    return jsonify({'success': True}), 200


# 修改配置更新接口
@app.route('/api/sql-configs/<name>', methods=['PUT'])
def update_sql_config(name):
    data = request.json
    configs = load_sql_config()
    
    # 查找原配置项
    index = next((i for i, c in enumerate(configs) if c['name'] == name), -1)
    if index == -1:
        return jsonify({'error': 'Config not found'}), 404

    # 检查新名称是否重复
    new_name = data.get('name', name)
    if new_name != name and any(c['name'] == new_name for c in configs):
        return jsonify({'error': '名称已存在'}), 400

    # 更新字段
    configs[index] = {
        **configs[index],
        "name": new_name,
        "filename_prefix": data.get('filename_prefix', configs[index]['filename_prefix']),
        "sql_template": data.get('sql', configs[index]['sql_template'])
    }
    
    save_sql_config(configs)
    return jsonify(configs[index])

# 分页执行SQL查询（优化版）
@app.route('/api/query-data', methods=['POST'])
def query_data():
    # 获取请求参数
    data = request.json
    sql_template = data.get('sql')
    page = int(data.get('page', 1))
    page_size = int(data.get('pageSize', 10))

    if not sql_template:
        return jsonify({'error': 'SQL语句不能为空'}), 400

    try:
        with DBConnection() as conn:
            # 获取总条数（使用参数化查询）
            count_sql = "SELECT COUNT(*) AS total FROM ({}) as subquery".format(sql_template)
            total = pd.read_sql(count_sql, conn).iloc[0]['total']
            
            # 分页计算
            total_pages = ceil(total / page_size)
            offset = (page - 1) * page_size
            
            # 执行分页查询
            paginated_sql = f"""
                {sql_template}
                LIMIT {page_size}
                OFFSET {offset}
            """
            df = pd.read_sql(paginated_sql, conn)
            
            # 处理结果数据
            results = {
                "data": df.to_dict(orient='records'),
                "meta": {
                    "pagination": {
                        "current_page": page,
                        "page_size": page_size,
                        "total": total,
                        "total_pages": total_pages
                    }
                }
            }
            
            return jsonify(results), 200

    except Exception as e:
        app.logger.error(f"SQL执行失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"查询执行失败: {str(e)}"
        }), 500

# 导出Excel接口（保持原有）
@app.route('/api/export-data', methods=['POST'])
def export_data():
    data = request.json
    sql_template = data.get('sql')
    
    try:
        with DBConnection() as conn:
            df = pd.read_sql(sql_template, conn)
            filename = f"export_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.xlsx"
            export_path = EXPORT_DIR / filename
            export_to_excel(df, export_path)
            return jsonify({
                'success': True,
                'download_url': f'/api/download/{filename}',
                'total': len(df)
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 下载文件
@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_file(
        EXPORT_DIR / filename,
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
