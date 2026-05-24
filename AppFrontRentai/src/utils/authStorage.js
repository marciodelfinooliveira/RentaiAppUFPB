const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'
const LEGACY_KEYS = [ACCESS_KEY, REFRESH_KEY]

function storage() {
  return sessionStorage
}

export function getAccessToken() {
  return storage().getItem(ACCESS_KEY)
}

export function getRefreshToken() {
  return storage().getItem(REFRESH_KEY)
}

export function setTokens(accessToken, refreshToken) {
  storage().setItem(ACCESS_KEY, accessToken)
  storage().setItem(REFRESH_KEY, refreshToken)
}

export function clearTokens() {
  storage().removeItem(ACCESS_KEY)
  storage().removeItem(REFRESH_KEY)
}

export function hasAccessToken() {
  return Boolean(getAccessToken())
}

export function migrateLegacyLocalStorageTokens() {
  if (typeof localStorage === 'undefined') return

  const legacyAccess = localStorage.getItem(ACCESS_KEY)
  const legacyRefresh = localStorage.getItem(REFRESH_KEY)

  if (legacyAccess && !getAccessToken()) {
    setTokens(legacyAccess, legacyRefresh || '')
  }

  for (const key of LEGACY_KEYS) {
    localStorage.removeItem(key)
  }
}
