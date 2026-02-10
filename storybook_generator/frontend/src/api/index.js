import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

// 项目相关API
export const projectsApi = {
  list: () => api.get('/api/projects/'),
  get: (id) => api.get(`/api/projects/${id}`),
  create: (data) => api.post('/api/projects/', data),
  update: (id, data) => api.put(`/api/projects/${id}`, data),
  delete: (id) => api.delete(`/api/projects/${id}`),
  uploadContent: (id, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/api/projects/${id}/upload-content`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  uploadStyleReference: (id, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/api/projects/${id}/upload-style-reference`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  reverseStylePrompt: (id) => api.post(`/api/projects/${id}/reverse-style-prompt`),
}

// 参考图相关API
export const referenceImagesApi = {
  generatePrompts: (projectId) => 
    api.post(`/api/reference-images/projects/${projectId}/generate-prompts`),
  list: (projectId, refType) => 
    api.get(`/api/reference-images/projects/${projectId}/references`, {
      params: { ref_type: refType }
    }),
  get: (id) => api.get(`/api/reference-images/${id}`),
  updatePrompt: (id, prompt) => api.put(`/api/reference-images/${id}/prompt`, { prompt }),
  generate: (id) => api.post(`/api/reference-images/${id}/generate`),
  checkStatus: (id) => api.post(`/api/reference-images/${id}/check-status`),
  delete: (id) => api.delete(`/api/reference-images/${id}`),
}

// 页面相关API
export const pagesApi = {
  planPages: (projectId, pagesPlans) =>
    api.post(`/api/pages/projects/${projectId}/plan-pages`, pagesPlans),
  list: (projectId) => api.get(`/api/pages/projects/${projectId}/pages`),
  get: (id) => api.get(`/api/pages/${id}`),
  generatePrompt: (id) => api.post(`/api/pages/${id}/generate-prompt`),
  generateAllPrompts: (projectId) =>
    api.post(`/api/pages/projects/${projectId}/generate-all-prompts`),
  updatePrompt: (id, prompt) => api.put(`/api/pages/${id}/prompt`, { prompt }),
  delete: (id) => api.delete(`/api/pages/${id}`),
}

// 图片生成相关API
export const imagesApi = {
  generate: (pageId, count = 3) =>
    api.post(`/api/images/pages/${pageId}/generate`, null, { params: { count } }),
  checkStatus: (imageId) => api.post(`/api/images/${imageId}/check-status`),
  autoSelect: (pageId) => api.post(`/api/images/pages/${pageId}/auto-select`),
  userSelect: (imageId) => api.post(`/api/images/${imageId}/select`),
  listPageImages: (pageId) => api.get(`/api/images/pages/${pageId}/images`),
  delete: (imageId) => api.delete(`/api/images/${imageId}`),
}

// 导出相关API
export const exportsApi = {
  exportPromptsExcel: (projectId) =>
    api.get(`/api/exports/projects/${projectId}/prompts/excel`, {
      responseType: 'blob',
    }),
  importPromptsExcel: (projectId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/api/exports/projects/${projectId}/prompts/import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  exportReferencesExcel: (projectId) =>
    api.get(`/api/exports/projects/${projectId}/references/excel`, {
      responseType: 'blob',
    }),
  downloadImage: (imageId) =>
    api.get(`/api/exports/images/${imageId}/download`, {
      responseType: 'blob',
    }),
  downloadFinalImage: (pageId) =>
    api.get(`/api/exports/pages/${pageId}/download-final`, {
      responseType: 'blob',
    }),
}

export default api
