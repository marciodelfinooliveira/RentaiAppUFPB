export const USER_ROLES = {
  GLOBAL_ADMIN: 'GLOBAL_ADMIN',
  DOCTOR_APS: 'DOCTOR_APS',
  DOCTOR_SPECIALIST: 'DOCTOR_SPECIALIST',
}

export const ROLE_LABELS = {
  GLOBAL_ADMIN: 'Administrador',
  DOCTOR_APS: 'Solicitante (APS)',
  DOCTOR_SPECIALIST: 'Especialista',
}

export const SPECIALTIES = [
  'Cardiologia',
  'Cirurgia Robótica',
  'Odontologia',
  'Doenças Raras',
  'Oxigenoterapia',
]

export const TELECONSULTATION_STATUS = {
  PENDENTE: 'PENDENTE',
  EM_ANDAMENTO: 'EM_ANDAMENTO',
  CONCLUIDA: 'CONCLUIDA',
  CANCELADA: 'CANCELADA',
}

export const STATUS_LABELS = {
  PENDENTE: 'Pendente',
  EM_ANDAMENTO: 'Em andamento',
  CONCLUIDA: 'Concluída',
  CANCELADA: 'Cancelada',
}

export const STATUS_FILTER_OPTIONS = [
  { value: '', label: 'Todos os status' },
  { value: TELECONSULTATION_STATUS.PENDENTE, label: 'Pendente' },
  { value: TELECONSULTATION_STATUS.EM_ANDAMENTO, label: 'Em andamento' },
  { value: TELECONSULTATION_STATUS.CONCLUIDA, label: 'Concluída' },
  { value: TELECONSULTATION_STATUS.CANCELADA, label: 'Cancelada' },
]

export const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/gif',
]

export const MAX_FILE_SIZE = 10 * 1024 * 1024
