export function buildTeleconsultationListParams({
  statusFilter = '',
  dateFrom = '',
  dateTo = '',
} = {}) {
  const params = {}
  if (statusFilter) params.status_filter = statusFilter
  if (dateFrom) params.start_date = dateFrom
  if (dateTo) params.end_date = dateTo
  return params
}
