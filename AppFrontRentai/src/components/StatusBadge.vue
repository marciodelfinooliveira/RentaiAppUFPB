<script setup>
import { computed } from 'vue'
import { STATUS_LABELS, TELECONSULTATION_STATUS } from '@/constants'

const props = defineProps({
  status: { type: String, required: true },
  showInProgressHint: { type: Boolean, default: false },
})

const label = computed(() => STATUS_LABELS[props.status] || props.status)
const cssClass = computed(
  () => `badge badge-${(props.status || '').toLowerCase()}`
)
const showHint = computed(
  () =>
    props.showInProgressHint &&
    props.status === TELECONSULTATION_STATUS.EM_ANDAMENTO
)
</script>

<template>
  <span class="status-badge-wrap">
    <span :class="cssClass" :key="status">{{ label }}</span>
    <span
      v-if="showHint"
      class="in-progress-hint"
      title="O especialista já visualizou esta solicitação"
    >
      <span class="in-progress-dot" aria-hidden="true" />
      Visualizada
    </span>
  </span>
</template>

<style scoped>
.status-badge-wrap {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

.in-progress-hint {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-success);
}

.in-progress-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-success);
  box-shadow: 0 0 0 2px rgba(45, 106, 79, 0.25);
}
</style>
