export function cleanCnpj(value) {
  return (value || '').replace(/[^a-zA-Z0-9]/g, '').toUpperCase()
}

export function validateCnpj(value) {
  const cleaned = cleanCnpj(value)
  if (cleaned.length !== 14) {
    return 'O CNPJ deve conter exatamente 14 caracteres alfanuméricos.'
  }
  return null
}

export function validateInstitutionNome(value) {
  const v = (value || '').trim()
  if (v.length < 3) return 'Nome deve ter pelo menos 3 caracteres.'
  if (!/^[A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+$/.test(v)) {
    return 'O nome deve conter apenas letras e espaços.'
  }
  return null
}

export function formatCnpjDisplay(value) {
  const c = cleanCnpj(value)
  if (c.length !== 14) return value || ''
  return `${c.slice(0, 2)}.${c.slice(2, 5)}.${c.slice(5, 8)}/${c.slice(8, 12)}-${c.slice(12)}`
}
