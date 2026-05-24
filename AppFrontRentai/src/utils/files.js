import { ALLOWED_FILE_TYPES, MAX_FILE_SIZE } from '@/constants'

export function validatePatientFiles(files, { required = true } = {}) {
  const fieldErrors = {}
  if (!files?.length) {
    if (required) {
      fieldErrors.files =
        'Envie pelo menos um documento (PDF ou imagem, máx. 10 MB cada).'
    }
    return fieldErrors
  }

  for (const file of files) {
    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      fieldErrors.files = `"${file.name}": tipo não permitido (PDF ou imagem).`
      return fieldErrors
    }
    if (file.size > MAX_FILE_SIZE) {
      fieldErrors.files = `"${file.name}": excede 10 MB.`
      return fieldErrors
    }
  }

  return fieldErrors
}

export function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function filterActiveFiles(list) {
  return (list || []).filter((f) => f.deleted_at == null)
}

export async function downloadPatientFile(file, filesApi) {
  const { data } = await filesApi.download(file.id)
  const url = URL.createObjectURL(data)
  const link = document.createElement('a')
  link.href = url
  link.download = file.nome_arquivo
  link.click()
  URL.revokeObjectURL(url)
}
