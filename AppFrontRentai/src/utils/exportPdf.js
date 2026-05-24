import { jsPDF } from 'jspdf'
import { formatDateTime } from './format'
import { STATUS_LABELS } from '@/constants'

export function exportTeleconsultationPdf({
  teleconsultation,
  patient,
  timeline,
  specialistName,
}) {
  const doc = new jsPDF()
  const t = teleconsultation
  let y = 20

  doc.setFontSize(16)
  doc.text('V4H — Resumo de Teleconsultoria', 14, y)
  y += 12

  doc.setFontSize(10)
  const lines = [
    `ID: ${t.id}`,
    `Especialidade: ${t.specialty}`,
    `Status: ${STATUS_LABELS[t.status] || t.status}`,
    `Paciente: ${patient?.nome || '—'}`,
    `Agendada: ${formatDateTime(t.scheduled_at)}`,
    `Hipótese diagnóstica: ${t.diagnostic_hypothesis}`,
    `História clínica: ${t.clinical_history}`,
    specialistName ? `Especialista: ${specialistName}` : '',
  ].filter(Boolean)

  for (const line of lines) {
    const wrapped = doc.splitTextToSize(line, 180)
    doc.text(wrapped, 14, y)
    y += wrapped.length * 6 + 4
    if (y > 270) {
      doc.addPage()
      y = 20
    }
  }

  if (timeline?.length) {
    y += 6
    doc.setFontSize(12)
    doc.text('Linha do tempo / Pareceres', 14, y)
    y += 8
    doc.setFontSize(10)
    for (const p of timeline) {
      const block = `[${formatDateTime(p.created_at)}] ${p.status_at_time}: ${p.comment}`
      const wrapped = doc.splitTextToSize(block, 180)
      doc.text(wrapped, 14, y)
      y += wrapped.length * 6 + 4
      if (y > 270) {
        doc.addPage()
        y = 20
      }
    }
  }

  doc.save(`teleconsultoria-${t.id.slice(0, 8)}.pdf`)
}
