import { cleanCpf, validateCpf } from '@/utils/cpf'
import { toDateInputValue } from '@/utils/format'

const NOME_REGEX = /^[A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+$/

export function filterActivePatients(list) {
  return (list || []).filter((p) => p.deleted_at == null)
}

export function normalizeBirthDateForApi(value) {
  if (!value) return null
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value
  return toDateInputValue(value) || null
}

export function validateDataNascimento(value, { required = true } = {}) {
  if (!value || !String(value).trim()) {
    return required ? 'A data de nascimento é obrigatória.' : null
  }

  const normalized = normalizeBirthDateForApi(value)
  const match = normalized?.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!match) {
    return 'A data de nascimento deve estar no formato AAAA-MM-DD.'
  }

  const year = parseInt(match[1], 10)
  const month = parseInt(match[2], 10)
  const day = parseInt(match[3], 10)
  const birth = new Date(year, month - 1, day)

  if (
    birth.getFullYear() !== year ||
    birth.getMonth() !== month - 1 ||
    birth.getDate() !== day
  ) {
    return 'Data de nascimento inválida.'
  }

  const hoje = new Date()
  hoje.setHours(0, 0, 0, 0)

  if (birth > hoje) {
    return 'A data de nascimento não pode ser no futuro.'
  }

  let idade = hoje.getFullYear() - year
  if (
    hoje.getMonth() < month - 1 ||
    (hoje.getMonth() === month - 1 && hoje.getDate() < day)
  ) {
    idade -= 1
  }
  if (idade > 120) {
    return 'A data de nascimento indica uma idade superior a 120 anos.'
  }

  return null
}

export function validatePatientNome(value) {
  const v = (value || '').trim()
  if (v.length < 3) return 'O nome deve ter entre 3 e 200 caracteres.'
  if (v.length > 200) return 'O nome deve ter no máximo 200 caracteres.'
  if (!NOME_REGEX.test(v)) {
    return 'O nome deve conter apenas letras e espaços.'
  }
  return null
}

export function validatePatientCreateForm(form) {
  const fieldErrors = {}
  const nomeErr = validatePatientNome(form.nome)
  const cpfErr = validateCpf(form.cpf)
  const birthErr = validateDataNascimento(form.data_nascimento, { required: true })
  if (nomeErr) fieldErrors.nome = nomeErr
  if (cpfErr) fieldErrors.cpf = cpfErr
  if (birthErr) fieldErrors.data_nascimento = birthErr
  return fieldErrors
}

export function validatePatientUpdateForm(form) {
  const fieldErrors = {}
  const nomeErr = validatePatientNome(form.nome)
  const cpfErr = validateCpf(form.cpf)
  const birthErr = validateDataNascimento(form.data_nascimento, { required: true })
  if (nomeErr) fieldErrors.nome = nomeErr
  if (cpfErr) fieldErrors.cpf = cpfErr
  if (birthErr) fieldErrors.data_nascimento = birthErr
  return fieldErrors
}

export function buildPatientBody(form) {
  return {
    nome: form.nome.trim(),
    cpf: cleanCpf(form.cpf),
    data_nascimento: normalizeBirthDateForApi(form.data_nascimento),
  }
}

export function buildPatientUpdatePayload(form, original) {
  const payload = {}
  const nome = form.nome.trim()
  const cpf = cleanCpf(form.cpf)
  const newBirth = normalizeBirthDateForApi(form.data_nascimento)
  const oldBirth = normalizeBirthDateForApi(original.data_nascimento)

  if (nome !== original.nome) payload.nome = nome
  if (cpf !== original.cpf) payload.cpf = cpf
  if (newBirth !== oldBirth) payload.data_nascimento = newBirth

  return payload
}
