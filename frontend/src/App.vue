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
        <el-button
          type="danger"
          :disabled="!selectedConfigName"
           @click="deleteSqlConfig"
          >
           <el-icon><Delete /></el-icon> 删除配置
        </el-button>
        <!-- 新增执行按钮 -->
        <el-button
          type="primary"
          :loading="executeLoading"
          @click="executeQuery"
          :disabled="!selectedConfigName"
        >
          <el-icon><MagicStick /></el-icon> {{ executeLoading ? '正在执行...' : '执行查询' }}
        </el-button>
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
      <!-- 新增数据展示表格 -->
      <el-table
        :data="tableData"
        stripe
        style="width: 100%; margin-top: 20px;"
        v-loading="executeLoading"
      >
        <el-table-column
          v-for="col in tableColumns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
        />
      </el-table>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handlePageChange"
        @current-change="handlePageChange"
        style="margin-top: 20px;"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  Upload,
  UploadFilled,  // 确认是否真实存在，或替换为其他图标
  Document,
  FolderOpened,
  Setting,
  Select
} from '@element-plus/icons-vue'
// 新增引入
import axios from 'axios'
// 新增引入图标和表格组件
import { MagicStick } from '@element-plus/icons-vue'
import { ElTable, ElTableColumn } from 'element-plus'

// CSV 上传相关状态
const selectedFile = ref(null)
const uploadLoading = ref(false)
const fileSize = ref('')

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

// 新增状态
const executeLoading = ref(false)
const tableData = ref([])
const tableColumns = ref([])
// 新增分页相关状态
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
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

// 修改执行方法
const executeQuery = async () => {
  try {
    executeLoading.value = true
    const response = await axios.post('/api/query-data', {
      sql: editSql.value,
      page: currentPage.value,
      pageSize: pageSize.value
    })
    
    // 处理返回数据
    tableData.value = response.data.data
    total.value =  response.data.pagination.total  // 修正为pagination.total
    
    // 自动生成表头
    if (tableData.value.length > 0) {
      tableColumns.value = Object.keys(tableData.value[0]).map(key => ({
        prop: key,
        label: key.replace(/_/g, ' ').replace(/(^\w|\s\w)/g, m => m.toUpperCase()), // 优化列名显示
        minWidth: 180
      }))
    }
    ElMessage.success(`查询到 ${total.value} 条数据`)

  } catch (error) {
    ElMessage.error(error.response?.data?.error || '执行失败')
  } finally {
    executeLoading.value = false
  }
}

// 分页变化处理
const handlePageChange = () => {
  if(editSql.value) {
    executeQuery()
  }
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
/* 优化表格样式 */
.el-table {
  margin-top: 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.el-table__header th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #495057;
}

.el-table__body td {
  padding: 12px 0;
  transition: background-color 0.3s;
}

.el-table--striped .el-table__body tr.el-table__row--striped td {
  background-color: #f8f9fa;
}

.el-pagination {
  justify-content: flex-end;
  padding: 16px 0;
}
</style>
