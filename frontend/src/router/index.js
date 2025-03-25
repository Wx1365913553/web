import { createRouter, createWebHistory } from 'vue-router'
import DataImport from '@/views/DataImport.vue'
import Query from '@/views/Query.vue'

const routes = [
  { path: '/', redirect: '/import' },
  { path: '/import', name: 'DataImport', component: DataImport },
  { path: '/query', name: 'Query', component: Query }
]

export default createRouter({
  history: createWebHistory(),
  routes
})