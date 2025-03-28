from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import json
import pandas as pdpy
from pathlib import Path
from utils.AutoDBImporter import DatabaseImporter
from utils.database import DBConnection
from utils.excel import export_to_excel
# 后端添加 CORS 支持
from flask_cors import CORS
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
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

# 保存SQL配置
def save_sql_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# 上传CSV并导入数据库
@app.route('/api/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV files allowed'}), 400
    
    try:
        # 添加调试日志
        print(f"收到文件: {file.filename}")
        temp_file_path = BASE_DIR / "temp" / file.filename
        os.makedirs(BASE_DIR / "temp", exist_ok=True)
        file.save(temp_file_path)
        print(f"文件保存路径: {temp_file_path}") # 添加日志打印来确认文件保存路径
        #df = pd.read_csv(file.stream)
        #print(f"数据预览:\n{df.head()}")
        # 保存文件到临时路径
        if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
            return jsonify({'error': '文件未成功保存'}), 500 # 检查文件是否存在
        
        # 使用 AutoDBImporter 导入文件
        importer = DatabaseImporter(db_config)
        report = importer.import_file(file_path=str(temp_file_path))
        
        # 删除临时文件
        #os.remove(temp_file_path)
        
        return jsonify(report), 200 if report['status'] == 'success' else 500
    except Exception as e:
        # 输出详细错误
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# 获取SQL配置列表
@app.route('/api/sql-configs', methods=['GET'])
def get_sql_configs():
    return jsonify(load_sql_config())

# 更新SQL配置接口
@app.route('/api/sql-configs/<name>', methods=['PUT'])
def update_sql_config(name):
    data = request.json
    configs = load_sql_config()
    
    # 查找对应配置项
    index = next((i for i, c in enumerate(configs) if c['name'] == name), -1)
    if index == -1:
        return jsonify({'error': 'Config not found'}), 404
    
    # 保留原始字段只更新sql
    configs[index]['sql'] = data['sql']
    save_sql_config(configs)
    return jsonify({'success': True, 'updated_config': configs[index]})
    
# 执行SQL并导出Excel
@app.route('/api/execute-sql', methods=['POST'])
def execute_sql():
    data = request.json
    sql_name = data.get('sql_name')
    params = data.get('params', {})
    
    configs = load_sql_config()
    sql_config = next((c for c in configs if c['name'] == sql_name), None)
    
    if not sql_config:
        return jsonify({'error': 'SQL config not found'}), 404
    
    try:
        with DBConnection() as conn:
            df = pd.read_sql(sql_config['sql'], conn, params=params)
            filename = f"{sql_config['name']}_{pd.Timestamp.now().strftime('%Y%m%d%H%M')}.xlsx"
            export_path = EXPORT_DIR / filename
            export_to_excel(df, export_path)
            return jsonify({
                'success': 'Export completed',
                'download_url': f'/api/download/{filename}'
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