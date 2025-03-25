<template>
  <el-card class="import-card">
    <h2>CSV 数据导入</h2>
    <el-upload
      class="upload-demo"
      :auto-upload="false"
      :on-change="handleFileChange"
      :show-file-list="false"
    >
      <template #trigger>
        <el-button type="primary" plain>
          <el-icon><Upload /></el-icon> 选择文件
        </el-button>
      </template>
      
      <el-button
        type="success"
        :disabled="!selectedFile"
        @click="submitUpload"
      >
        <el-icon><UploadFilled /></el-icon> 开始导入
      </el-button>
    </el-upload>

    <div v-if="selectedFile" class="file-info">
      <el-icon><Document /></el-icon>
      {{ selectedFile.name }} ({{ fileSize }})
    </div>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/api'
import { Upload, UploadFilled, Document } from '@element-plus/icons-vue'

const selectedFile = ref(null)
const fileSize = ref('')

const handleFileChange = (file) => {
  selectedFile.value = file.raw
  fileSize.value = (file.size / 1024 / 1024).toFixed(2) + ' MB'
}

const submitUpload = async () => {
  try {
    const res = await api.uploadCSV(selectedFile.value)
    ElMessage.success(res.data.success)
    selectedFile.value = null
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '上传失败')
  }
}
</script>

<style scoped>
.import-card {
  margin: 20px;
  padding: 20px;
}

.upload-demo {
  margin: 20px 0;
}

.file-info {
  margin-top: 10px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>