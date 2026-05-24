<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { pareceresApi } from '@/api'
import { parseApiError } from '@/utils/errors'

const route = useRoute()
const router = useRouter()

const teleconsultationId = ref('')
const comment = ref('')
const error = ref('')
const loading = ref(false)

onMounted(() => {
  teleconsultationId.value =
    route.query.teleconsultation_id || route.params.id || ''
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await pareceresApi.create({
      teleconsultation_id: teleconsultationId.value,
      comment: comment.value,
    })
    router.push(`/teleconsultations/${teleconsultationId.value}`)
  } catch (e) {
    error.value = parseApiError(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <div class="page-header">
      <h1>Registrar parecer</h1>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <form class="card" @submit.prevent="submit">
      <div class="form-group">
        <label>ID da teleconsultoria</label>
        <input v-model="teleconsultationId" required readonly />
      </div>
      <div class="form-group">
        <label>Parecer / comentário clínico</label>
        <textarea v-model="comment" required rows="6" />
      </div>
      <button type="submit" class="btn btn-primary" :disabled="loading">
        {{ loading ? 'Salvando…' : 'Registrar parecer' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.hint { color: var(--color-muted); font-size: 0.85rem; margin-bottom: 1rem; }
</style>
