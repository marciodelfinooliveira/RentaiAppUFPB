import { USER_ROLES } from '@/constants'

const NOME_REGEX = /^[A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+$/
const PASSWORD_SPECIAL = /[!@#$%^&*(),.?":{}|<>]/

export function validateUserNome(value) {
  const v = (value || '').trim()
  if (v.length < 5) return 'O nome deve ter entre 5 e 100 caracteres.'
  if (v.length > 100) return 'O nome deve ter no máximo 100 caracteres.'
  if (!NOME_REGEX.test(v)) {
    return 'O nome deve conter apenas letras e espaços, sem números ou caracteres especiais.'
  }
  return null
}

export function validatePassword(value, { required = true } = {}) {
  if (!value) {
    return required ? 'Senha é obrigatória.' : null
  }
  if (value.length < 8 || value.length > 128) {
    return 'A senha deve ter entre 8 e 128 caracteres.'
  }
  if (!/[A-Z]/.test(value)) {
    return 'A senha deve conter pelo menos uma letra maiúscula.'
  }
  if (!/[0-9]/.test(value)) {
    return 'A senha deve conter pelo menos um número.'
  }
  if (!PASSWORD_SPECIAL.test(value)) {
    return 'A senha deve conter pelo menos um caractere especial.'
  }
  return null
}

export function validateVerifyCode(value) {
  if (!/^\d{6}$/.test(value || '')) {
    return 'O código deve ser numérico e conter exatamente 6 dígitos.'
  }
  return null
}

export function validateDoctorFields({ role, specialty, institutionId }) {
  const errors = {}

  if (role === USER_ROLES.DOCTOR_SPECIALIST && !specialty) {
    errors.specialty = 'A especialidade é obrigatória para o perfil Especialista.'
  }

  if (role !== USER_ROLES.DOCTOR_SPECIALIST && specialty) {
    errors.specialty =
      'Apenas médicos com perfil Especialista podem possuir especialidade.'
  }

  if (
    (role === USER_ROLES.DOCTOR_APS || role === USER_ROLES.DOCTOR_SPECIALIST) &&
    !institutionId
  ) {
    errors.institution_id = 'O vínculo com uma instituição é obrigatório para médicos.'
  }

  return errors
}

export function validateUserCreateForm(form) {
  const fieldErrors = {}
  const nomeErr = validateUserNome(form.nome)
  const passErr = validatePassword(form.password, { required: true })
  if (nomeErr) fieldErrors.nome = nomeErr
  if (passErr) fieldErrors.password = passErr
  Object.assign(fieldErrors, validateDoctorFields(form))
  return fieldErrors
}

export function validateUserUpdateForm(form, role) {
  const fieldErrors = {}
  const nomeErr = validateUserNome(form.nome)
  if (nomeErr) fieldErrors.nome = nomeErr
  if (form.password) {
    const passErr = validatePassword(form.password, { required: false })
    if (passErr) fieldErrors.password = passErr
  }
  Object.assign(
    fieldErrors,
    validateDoctorFields({
      role,
      specialty: form.specialty || null,
      institutionId: form.institution_id,
    })
  )
  return fieldErrors
}
