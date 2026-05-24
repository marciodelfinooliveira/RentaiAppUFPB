<script setup>
import { computed } from 'vue'
import {
  buildAiAuditTooltip,
  formatAiScoreDisplay,
  hasAiAuditData,
} from '@/utils/aiDocumentValidation'

const props = defineProps({
  file: { type: Object, required: true },
})

const visible = computed(() => hasAiAuditData(props.file))
const label = computed(() => formatAiScoreDisplay(props.file?.ai_score))
const title = computed(() => buildAiAuditTooltip(props.file))
</script>

<template>
  <span
    v-if="visible"
    class="ai-audit-tag"
    :title="title"
  >
    IA {{ label }}
  </span>
</template>

<style scoped>
.ai-audit-tag {
  display: inline-block;
  margin-left: 0.35rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  background: #e8f4ea;
  color: var(--color-success);
  cursor: help;
  vertical-align: middle;
}
</style>
