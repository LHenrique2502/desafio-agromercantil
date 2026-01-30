export type Truck = {
  id: number
  license_plate: string
  brand: string
  model: string
  manufacturing_year: number
  fipe_price: string
}

export type FipeItem = { code: string; name: string }

type ApiError = {
  error?: string
  detail?: string
} & Record<string, unknown>

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })

  const isJson = res.headers.get('content-type')?.includes('application/json')
  const data = (isJson ? await res.json() : await res.text()) as unknown

  if (!res.ok) {
    const d = data as ApiError
    const message =
      (typeof d === 'object' && d && (d.error || d.detail)) ||
      `Erro ao chamar API (${res.status})`
    throw new Error(String(message))
  }

  return data as T
}

export function listTrucks() {
  return request<Truck[]>('/trucks/')
}

export function getTruck(id: number) {
  // Não existe GET /trucks/{id}/ no backend; usamos lista e filtramos no client
  // (para manter o escopo do desafio com endpoints mínimos).
  return listTrucks().then((items) => {
    const found = items.find((t) => t.id === id)
    if (!found) throw new Error('Caminhão não encontrado.')
    return found
  })
}

export function createTruck(payload: {
  license_plate: string
  brand: string
  model: string
  manufacturing_year: number
}) {
  return request<Truck>('/trucks/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateTruck(
  id: number,
  payload: { brand: string; model: string; manufacturing_year: number },
) {
  return request<Truck>(`/trucks/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function fipeBrands() {
  return request<FipeItem[]>('/fipe/brands/')
}

export function fipeModels(brand: string) {
  const qs = new URLSearchParams({ brand })
  return request<FipeItem[]>(`/fipe/models/?${qs.toString()}`)
}

export function fipeYears(brand: string, model: string) {
  const qs = new URLSearchParams({ brand, model })
  return request<FipeItem[]>(`/fipe/years/?${qs.toString()}`)
}

