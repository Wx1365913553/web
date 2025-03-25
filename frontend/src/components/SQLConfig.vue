<template>
  <el-table :data="sqlConfigs" stripe>
    <el-table-column prop="name" label="配置名称" />
    <el-table-column prop="description" label="描述" />
    <el-table-column label="操作">
      <template #default="{ row }">
        <el-button 
          type="primary" 
          @click="executeSql(row.name)"
          :loading="loading[row.name]"
        >
          执行
        </el-button>
        <el-button 
          v-if="row.params" 
          @click="showParamDialog(row)"
        >
          参数设置
        </el-button>
      </template>
    </el-table-column>
  </el-table>

  <!-- 参数对话框 -->
  <el-dialog v-model="paramDialog.visible" :title="paramDialog.title">
    <el-form>
      <el-form-item 
        v-for="param in paramDialog.params" 
        :key="param" 
        :label="param"
      >
        <el-input v-model="paramData[param]" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="paramDialog.visible = false">取消</el-button>
      <el-button type="primary" @click="confirmExecute">
        确认执行
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/api'

const sqlConfigs = ref([])
const loading = reactive({})
const paramDialog = reactive({
  visible: false,
  title: '',
  params: []
})
const paramData = reactive({})
let currentConfig = null

onMounted(async () => {
  try {
    const res = await api.getSqlConfigs()
    sqlConfigs.value = res.data
  } catch (err) {
    ElMessage.error('获取配置失败')
  }
})

const executeSql = async (name) => {
  try {
    loading[name] = true
    const res = await api.executeSql(name)
    window.location.href = res.data.download_url
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '执行失败')
  } finally {
    loading[name] = false
  }
}

const showParamDialog = (config) => {
  currentConfig = config
  paramDialog.title = `参数设置 - ${config.name}`
  paramDialog.params = Object.keys(config.params || {})
  paramDialog.visible = true
}

const confirmExecute = () => {
  paramDialog.visible = false
  // 调用执行方法时带上参数
  executeSql(currentConfig.name, paramData)
}
</script>