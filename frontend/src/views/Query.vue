<template>
  <div class="query-page">
    <h2>数据查询</h2>
    <SqlConfig />
    
    <el-divider />
    
    <div class="custom-sql">
      <el-input
        v-model="customSql"
        type="textarea"
        :rows="4"
        placeholder="输入自定义 SQL 语句"
      />
      <el-button
        type="primary"
        :loading="customLoading"
        @click="executeCustomSql"
      >
        <el-icon><MagicStick /></el-icon> 执行查询
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import SqlConfig from '@/components/SqlConfig.vue'
import api from '@/api/api'
import { MagicStick } from '@element-plus/icons-vue'

const customSql = ref('')
const customLoading = ref(false)

const executeCustomSql = async () => {
  if (!customSql.value.trim()) {
    ElMessage.warning('请输入 SQL 语句')
    return
  }
  
  try {
    customLoading.value = true
    const res = await api.executeSql('custom', { sql: customSql.value })
    window.location.href = res.data.download_url
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '执行失败')
  } finally {
    customLoading.value = false
  }
}
</script>

<style scoped>
.query-page {
  margin: 20px;
  padding: 20px;
}

.custom-sql {
  margin-top: 30px;

  .el-textarea {
    margin-bottom: 15px;
  }
}
</style>