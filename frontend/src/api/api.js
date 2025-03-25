import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:5000',  // 确保路径正确
  timeout: 10000
})

export default {
  // 上传CSV
  uploadCSV(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload', formData, {  // 修改这里
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 获取SQL配置
  getSqlConfigs() {
    return api.get('/sql-configs')
  },

  // 执行SQL
  executeSql(name) {
    return api.post('/execute-sql', { sql_name: name })
  }
}
