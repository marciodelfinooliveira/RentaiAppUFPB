import { SPECIALTIES } from '@/constants'

const MAX_SCHEDULE_DAYS_AHEAD = 730

export function datetimeLocalNow() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function datetimeLocalMaxAhead() {
  const d = new Date()
  d.setDate(d.getDate() + MAX_SCHEDULE_DAYS_AHEAD)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function validateScheduledAt(value) {
  if (!value || !String(value).trim()) {
    return 'A data/hora da consulta é obrigatória.'
  }

  const scheduled = new Date(value)
  if (Number.isNaN(scheduled.getTime())) {
    return 'Data/hora inválida.'
  }

  const now = new Date()
  if (scheduled < now) {
    return 'A data da consulta não pode ser no passado.'
  }

  const limit = new Date()
  limit.setDate(limit.getDate() + MAX_SCHEDULE_DAYS_AHEAD)
  if (scheduled > limit) {
    return 'A consulta não pode ser agendada para mais de 2 anos no futuro.'
  }

  return null
}

export function validateDiagnosticHypothesis(value) {
  const v = (value || '').trim()
  if (v.length < 5) {
    return 'A hipótese diagnóstica deve ter entre 5 e 500 caracteres.'
  }
  if (v.length > 500) {
    return 'A hipótese diagnóstica deve ter no máximo 500 caracteres.'
  }
  return null
}

export function validateClinicalHistory(value) {
  const v = (value || '').trim()
  if (v.length < 10) {
    return 'A história clínica deve ter entre 10 e 2000 caracteres.'
  }
  if (v.length > 2000) {
    return 'A história clínica deve ter no máximo 2000 caracteres.'
  }
  return null
}

export function validateSpecialty(value) {
  if (!value || !SPECIALTIES.includes(value)) {
    return 'Selecione uma especialidade válida.'
  }
  return null
}

export function validateTeleconsultationCreateForm(form) {
  const fieldErrors = {}

  if (!form.patient_id) {
    fieldErrors.patient_id = 'Selecione um paciente.'
  }
  if (!form.specialist_doctor_id) {
    fieldErrors.specialist_doctor_id = 'Selecione um especialista.'
  }

  const specialtyErr = validateSpecialty(form.specialty)
  if (specialtyErr) fieldErrors.specialty = specialtyErr

  const hypothesisErr = validateDiagnosticHypothesis(form.diagnostic_hypothesis)
  if (hypothesisErr) fieldErrors.diagnostic_hypothesis = hypothesisErr

  const historyErr = validateClinicalHistory(form.clinical_history)
  if (historyErr) fieldErrors.clinical_history = historyErr

  const scheduleErr = validateScheduledAt(form.scheduled_at)
  if (scheduleErr) fieldErrors.scheduled_at = scheduleErr

  return fieldErrors
}

export function buildTeleconsultationBody(form, fromDatetimeLocalValue) {
  return {
    patient_id: form.patient_id,
    specialist_doctor_id: form.specialist_doctor_id,
    specialty: form.specialty,
    diagnostic_hypothesis: form.diagnostic_hypothesis.trim(),
    clinical_history: form.clinical_history.trim(),
    scheduled_at: fromDatetimeLocalValue(form.scheduled_at),
  }
}
