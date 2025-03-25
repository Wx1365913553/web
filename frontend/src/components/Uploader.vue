<template>
  <el-upload
    action="/api/upload"
    :limit="1"
    :on-success="handleSuccess"
    :on-error="handleError"
    :file-list="fileList"
  >
    <el-button type="primary">点击上传CSV文件</el-button>
    <template #tip>仅支持CSV格式，最大文件50MB</template>
  </el-upload>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const fileList = ref([])

const handleSuccess = () => {
  ElMessage.success('文件上传成功！')
  fileList.value = []
}

const handleError = (err) => {
  ElMessage.error(`上传失败: ${err.message}`)
}
</script>