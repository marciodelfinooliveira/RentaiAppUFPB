import { api } from './client'

export const usersApi = {
  register: (body) => api.post('/users/', body),
  verify: (body) => api.post('/users/verify', body),
  login: (email, password) => {
    const params = new URLSearchParams()
    params.append('username', email)
    params.append('password', password)
    return api.post('/users/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  me: () => api.get('/users/me'),
  updateMe: (body) => api.patch('/users/me', body),
  logout: (refreshToken) =>
    api.post('/users/logout', { refresh_token: refreshToken }),
  specialists: () => api.get('/users/specialists'),
}

export const institutionsApi = {
  list: () => api.get('/institutions/'),
  create: (body) => api.post('/institutions/', body),
  update: (id, body) => api.patch(`/institutions/${id}`, body),
  remove: (id) => api.delete(`/institutions/${id}`),
}

export const patientsApi = {
  list: () => api.get('/patients/'),
  create: (patientBody, files = []) => {
    const form = new FormData()
    form.append('patient_data', JSON.stringify(patientBody))
    for (const file of files) {
      form.append('files', file)
    }
    return api.post('/patients/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  update: (id, body) => api.patch(`/patients/${id}`, body),
  remove: (id) => api.delete(`/patients/${id}`),
}

export const filesApi = {
  upload: (patientId, file) => {
    const form = new FormData()
    form.append('patient_id', patientId)
    form.append('file', file)
    return api.post('/files/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  remove: (fileId) => api.delete(`/files/${fileId}`),
  download: (fileId) =>
    api.get(`/files/${fileId}/download`, { responseType: 'blob' }),
}

export const teleconsultationsApi = {
  list: (params = {}) => api.get('/teleconsultations/', { params }),
  get: (id) => api.get(`/teleconsultations/${id}`),
  create: (teleconsultationBody, files = []) => {
    const form = new FormData()
    form.append('data_in', JSON.stringify(teleconsultationBody))
    for (const file of files) {
      form.append('files', file)
    }
    return api.post('/teleconsultations/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  cancel: (id, body) => api.patch(`/teleconsultations/${id}/cancel`, body),
}

export const pareceresApi = {
  create: (body) => api.post('/pareceres/', body),
  timeline: (teleId) => api.get(`/pareceres/${teleId}/timeline`),
}
