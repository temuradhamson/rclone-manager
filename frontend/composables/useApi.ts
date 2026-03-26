export function useApi() {
  const config = useRuntimeConfig()
  const base = config.public.apiBase

  async function get<T>(url: string, params?: Record<string, any>): Promise<T> {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return await $fetch<T>(`${base}${url}${query}`)
  }

  async function post<T>(url: string, body?: any): Promise<T> {
    return await $fetch<T>(`${base}${url}`, { method: 'POST', body })
  }

  async function put<T>(url: string, body?: any): Promise<T> {
    return await $fetch<T>(`${base}${url}`, { method: 'PUT', body })
  }

  async function del(url: string): Promise<void> {
    await $fetch(`${base}${url}`, { method: 'DELETE' })
  }

  async function patch<T>(url: string, body?: any): Promise<T> {
    return await $fetch<T>(`${base}${url}`, { method: 'PATCH', body })
  }

  return { get, post, put, del, patch }
}
