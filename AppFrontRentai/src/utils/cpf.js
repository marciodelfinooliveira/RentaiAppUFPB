export function cleanCpf(value) {
  return (value || '').replace(/\D/g, '')
}

export function validateCpf(value) {
  const cpf = cleanCpf(value)

  if (cpf.length !== 11) {
    return 'O CPF deve conter exatamente 11 dígitos.'
  }

  if (cpf === cpf[0].repeat(11)) {
    return 'CPF inválido.'
  }

  for (let i = 9; i < 11; i++) {
    let sum = 0
    for (let num = 0; num < i; num++) {
      sum += parseInt(cpf[num], 10) * (i + 1 - num)
    }
    let digit = (sum * 10) % 11
    if (digit === 10) digit = 0
    if (digit !== parseInt(cpf[i], 10)) {
      return 'CPF inválido.'
    }
  }

  return null
}

export function formatCpfDisplay(value) {
  const cpf = cleanCpf(value)
  if (cpf.length !== 11) return value || ''
  return `${cpf.slice(0, 3)}.${cpf.slice(3, 6)}.${cpf.slice(6, 9)}-${cpf.slice(9)}`
}
