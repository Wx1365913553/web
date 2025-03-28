<template>
  <div class="container">
    <!-- 标题 -->
    <h1 style="margin-bottom: 30px;">飞检医保数据管理平台</h1>

    <!-- CSV 数据导入模块 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <el-icon><Upload /></el-icon>
          <span>数据导入</span>
        </div>
      </template>

      <el-upload
        class="upload-box"
        :auto-upload="false"
        :on-change="handleFileChange"
        :show-file-list="false"
      >
        <template #trigger>
          <el-button type="primary">
            <el-icon><FolderOpened /></el-icon> 选择CSV文件
          </el-button>
        </template>

        <el-button
          type="success"
          :loading="uploadLoading"
          :disabled="!selectedFile"
          @click="handleUpload"
        >
          <el-icon><UploadFilled /></el-icon> {{ uploadLoading ? '正在导入...' : '开始导入' }}
        </el-button>
      </el-upload>

      <div v-if="selectedFile" class="file-info">
        <el-icon><Document /></el-icon>
        {{ selectedFile.name }} ({{ fileSize }})
      </div>
    </el-card>

    <!-- SQL 模板管理 -->
  <!-- SQL模板管理部分 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <el-icon><Setting /></el-icon>
          <span>SQL模板管理</span>
        </div>
      </template>

      <el-select 
        v-model="selectedConfigName"
        placeholder="选择SQL模板"
        @change="handleConfigChange"
        style="width: 100%; margin-bottom: 15px;"
      >
        <el-option
          v-for="(config, index) in sqlConfigs"
          :key="config.name"
          :label="`${config.name}、${config.filename_prefix}`"
          :value="config.name"
        />
      </el-select>



      <el-input
        v-model="editSql"
        type="textarea"
        :rows="10"
        placeholder="编辑SQL语句"
        resize="none"
      />

      <div class="action-bar" style="margin-top: 15px;">
        <el-button
          type="primary"
          @click="showAddConfigForm"
        >
          <el-icon><Plus /></el-icon> 新增SQL配置
        </el-button>
        <el-button
          type="primary"
          :loading="saveLoading"
          @click="saveSqlConfig"
        >
          <el-icon><Select /></el-icon> 保存修改
        </el-button>
              <div class="action-bar" style="margin-top: 15px;">
                <el-button
                  type="danger"
                  :disabled="!selectedConfigName"
                  @click="deleteSqlConfig"
                >
                  <el-icon><Delete /></el-icon> 删除配置
                </el-button>
              </div>
    </el-card>
    <!-- 修改配置编辑表单 -->
    <el-dialog title="编辑SQL配置" v-model="editDialogVisible">
      <el-form>
        <el-form-item label="名称">
          <el-input v-model="editForm.name"></el-input>
        </el-form-item>
        <el-form-item label="文件名前缀">
          <el-input v-model="editForm.filename_prefix"></el-input>
        </el-form-item>
        <el-form-item label="SQL模板">
          <el-input v-model="editForm.sql_template" type="textarea" :rows="10"/>
        </el-form-item>
      </el-form>
    </el-dialog>
    <el-dialog
      title="新增SQL配置"
      v-model="addConfigFormVisible"
      width="30%"
    >
      <el-form :model="newConfig">
        <el-form-item label="名称" :label-width="formLabelWidth">
          <el-input v-model="newConfigName" autocomplete="off"></el-input>
        </el-form-item>
        <el-form-item label="文件名前缀" :label-width="formLabelWidth">
          <el-input v-model="newConfigFilenamePrefix" autocomplete="off"></el-input>
        </el-form-item>
        <el-form-item label="SQL模板" :label-width="formLabelWidth">
          <el-input
            v-model="newConfigSqlTemplate"
            type="textarea"
            :rows="4"
            placeholder="编辑SQL模板"
            resize="none"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addConfigFormVisible = false">取 消</el-button>
          <el-button
            type="primary"
            :loading="addConfigLoading"
            @click="saveNewSqlConfig"
          >确 定</el-button>
        </span>
      </template>
    </el-dialog>
    <!-- SQL 执行模块 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <el-icon><Search /></el-icon>
          <span>数据查询</span>
        </div>
      </template>

      <el-input
        v-model="sqlQuery"
        type="textarea"
        :rows="5"
        placeholder="输入 SQL 查询语句，示例：SELECT * FROM patients WHERE age > 18"
        clearable
      />

      <div class="action-bar">
        <el-button
          type="primary"
          :loading="executeLoading"
          @click="executeQuery"
        >
          <el-icon><MagicStick /></el-icon> {{ executeLoading ? '正在执行...' : '执行查询' }}
        </el-button>

        <el-button @click="showExample">
          <el-icon><InfoFilled /></el-icon> 查看示例
        </el-button>
      </div>

      <div v-if="downloadUrl" class="download-area">
        <el-link type="success" :href="downloadUrl" target="_blank">
          <el-icon><Download /></el-icon> 点击下载结果文件
        </el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  Upload,
  UploadFilled,
  Document,
  FolderOpened,
  Search,
  MagicStick,
  InfoFilled,
  Download,
  Setting,
  Select
} from '@element-plus/icons-vue'
import axios from 'axios'

// CSV 上传相关状态
const selectedFile = ref(null)
const uploadLoading = ref(false)
const fileSize = ref('')

// SQL 执行相关状态
const sqlQuery = ref('')
const executeLoading = ref(false)
const downloadUrl = ref('')

// SQL 模板管理相关状态
const sqlConfigs = ref([])
const selectedConfigName = ref('')  // 改为存储选中的配置名称
const editSql = ref('')
const saveLoading = ref(false)
// 新增SQL配置相关状态
const newConfigName = ref('')
const newConfigFilenamePrefix = ref('')
const newConfigSqlTemplate = ref('')
const addConfigLoading = ref(false)
const addConfigFormVisible = ref(false)
// 添加编辑方法
const editDialogVisible = ref(false)
const editForm = ref({})


// 显示新增配置表单
const showAddConfigForm = () => {
  addConfigFormVisible.value = true
}

// 处理文件选择
const handleFileChange = (file) => {
  selectedFile.value = file.raw
  fileSize.value = (file.size / 1024 / 1024).toFixed(2) + ' MB'
}

// 执行文件上传
const handleUpload = async () => {
  if (!selectedFile.value) return

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    uploadLoading.value = true
    const res = await axios.post('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success(res.data.success)
    selectedFile.value = null
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '导入失败')
  } finally {
    uploadLoading.value = false
  }
}

// 加载SQL配置
const loadSqlConfigs = async () => {
  try {
    const res = await axios.get('/api/sql-configs')
    // 处理可能的旧格式数据
    sqlConfigs.value = Array.isArray(res.data) ? res.data : Object.values(res.data)
  } catch (err) {
    ElMessage.error('加载SQL配置失败')
  }
}

// 修改初始化加载方法
onMounted(async () => {
  try {
    const res = await axios.get('/api/sql-configs')
    // 确保数据结构为数组
    sqlConfigs.value = Array.isArray(res.data) ? res.data : []
  } catch (err) {
    ElMessage.error('加载SQL配置失败')
  }
})


// 处理模板选择变化
const handleConfigChange = (configName) => {
  const selected = sqlConfigs.value.find(c => c.name === configName)
  if (selected) {
    editSql.value = selected.sql_template
  } else {
    editSql.value = ''
  }
}
// 修改保存SQL配置方法
const saveSqlConfig = async () => {
  if (!selectedConfigName.value || !editSql.value.trim()) {
    ElMessage.warning('请选择模板并输入有效SQL')
    return
  }

  try {
    saveLoading.value = true
    // 修正请求字段名为 sql_template
    await axios.put(`/api/sql-configs/${selectedConfigName.value}`, {
      sql_template: editSql.value
    })
    
    // 更新本地配置
    const index = sqlConfigs.value.findIndex(c => c.name === selectedConfigName.value)
    if (index > -1) {
      sqlConfigs.value[index].sql_template = editSql.value
    }
    ElMessage.success('模板保存成功')
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '保存失败')
  } finally {
    saveLoading.value = false
  }
}


// 保存新增SQL配置
const saveNewSqlConfig = async () => {
  if (!newConfigName.value.trim() || !newConfigFilenamePrefix.value.trim() || !newConfigSqlTemplate.value.trim()) {
    ElMessage.warning('请填写所有字段');
    return;
  }

  try {
    addConfigLoading.value = true;
    const res = await axios.post('/api/sql-configs', {
      name: newConfigName.value,
      filename_prefix: newConfigFilenamePrefix.value,
      sql_template: newConfigSqlTemplate.value,
      codes: []  // 或者根据需要添加默认值
    })
    
    // 更新本地配置
    if (res.data.success) {
        sqlConfigs.value.push(res.data.data)
        ElMessage.success('新增模板成功')
        addConfigFormVisible.value = false
        // 强制刷新下拉框
        const latest = await axios.get('/api/sql-configs')
        sqlConfigs.value = latest.data
      }
    } catch (err) {
      ElMessage.error(err.response?.data?.error || '新增失败')
    } finally {
      addConfigLoading.value = false
      // 清空表单放到成功逻辑中
    }
}
//编辑配置相关方法
const handleEdit = (config) => {
  editForm.value = { ...config }
  editDialogVisible.value = true
}

const saveEdit = async () => {
  try {
    await axios.put(`/api/sql-configs/${editForm.value.originalName}`, {
      name: editForm.value.name,
      filename_prefix: editForm.value.filename_prefix,
      sql: editForm.value.sql_template
    })
    // 刷新列表
    const res = await axios.get('/api/sql-configs')
    sqlConfigs.value = res.data
    editDialogVisible.value = false
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '保存失败')
  }
}

// 添加删除方法
const deleteSqlConfig = async () => {
  if (!selectedConfigName.value) {
    ElMessage.warning('请选择要删除的模板')
    return
  }
  
  try {
    await axios.delete(`/api/sql-configs/${selectedConfigName.value}`)
    ElMessage.success('删除成功')
    // 重新加载配置
    const res = await axios.get('/api/sql-configs')
    sqlConfigs.value = res.data
    selectedConfigName.value = ''
    editSql.value = ''
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '删除失败')
  }
}

// 执行SQL查询
const executeQuery = async () => {
  if (!sqlQuery.value.trim()) {
    ElMessage.warning('请输入查询语句')
    return
  }

  try {
    executeLoading.value = true
    const res = await axios.post('/api/execute-sql', {
      sql_name: 'custom',
      params: { sql: sqlQuery.value }
    })
    downloadUrl.value = res.data.download_url
    ElMessage.success('查询执行成功，点击下方链接下载结果')
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '执行失败')
    downloadUrl.value = ''
  } finally {
    executeLoading.value = false
  }
}

// 显示示例语句
const showExample = () => {
  sqlQuery.value = `-- 示例1：查询所有患者信息
SELECT * FROM patients;

-- 示例2：统计各科室就诊人数
SELECT department, COUNT(*) AS total 
FROM medical_records 
GROUP BY department;`
}
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
}

.section-card {
  margin-bottom: 30px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: bold;
}

.upload-box {
  margin: 15px 0;
  display: flex;
  gap: 10px;
  align-items: center;
}

.file-info {
  margin-top: 10px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 6px;
}

.action-bar {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.download-area {
  margin-top: 15px;
  padding: 10px;
  background: #f6ffed;
  border-radius: 4px;
}
</style>
