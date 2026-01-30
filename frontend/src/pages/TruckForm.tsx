import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import {
  createTruck,
  fipeBrands,
  fipeModels,
  fipeYears,
  getTruck,
  updateTruck,
  type FipeItem,
} from '../services/api'

const PLATE_RE = /^(?:[A-Z]{3}-?\d{4}|[A-Z]{3}\d[A-Z]\d{2})$/

function normalizePlate(value: string) {
  return value.trim().toUpperCase().replaceAll(' ', '')
}

function parseYearFromLabel(label: string) {
  const m = /^\s*(\d{4})/.exec(label)
  if (!m) return null
  return Number(m[1])
}

type FormState = {
  license_plate: string
  brand: string // FIPE code (preferência), mas pode ser nome
  model: string // FIPE code (preferência), mas pode ser nome
  manufacturing_year: string // label ou ano
}

export function TruckForm() {
  const nav = useNavigate()
  const params = useParams()
  const id = params.id ? Number(params.id) : null
  const isEdit = Number.isFinite(id) && id !== null

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [brands, setBrands] = useState<FipeItem[]>([])
  const [models, setModels] = useState<FipeItem[]>([])
  const [years, setYears] = useState<FipeItem[]>([])

  const [form, setForm] = useState<FormState>({
    license_plate: '',
    brand: '',
    model: '',
    manufacturing_year: '',
  })

  const [touched, setTouched] = useState<Record<string, boolean>>({})

  const selectedBrand = useMemo(() => brands.find((b) => b.code === form.brand), [brands, form.brand])
  const selectedModel = useMemo(() => models.find((m) => m.code === form.model), [models, form.model])
  const selectedYear = useMemo(() => years.find((y) => y.code === form.manufacturing_year), [years, form.manufacturing_year])

  function setField<K extends keyof FormState>(k: K, v: FormState[K]) {
    setForm((s) => ({ ...s, [k]: v }))
  }

  function fieldError(key: keyof FormState): string | null {
    if (!touched[key]) return null
    if (key === 'license_plate') {
      if (!form.license_plate.trim()) return 'Campo obrigatório.'
      const plate = normalizePlate(form.license_plate)
      if (!PLATE_RE.test(plate)) return 'Placa inválida. Use AAA-1234 ou AAA1A23.'
      return null
    }
    if (key === 'brand') return form.brand ? null : 'Campo obrigatório.'
    if (key === 'model') return form.model ? null : 'Campo obrigatório.'
    if (key === 'manufacturing_year') return form.manufacturing_year ? null : 'Campo obrigatório.'
    return null
  }

  const canSubmit = useMemo(() => {
    const plateOk = isEdit ? true : PLATE_RE.test(normalizePlate(form.license_plate))
    return plateOk && !!form.brand && !!form.model && !!form.manufacturing_year
  }, [form, isEdit])

  async function loadBrands() {
    const data = await fipeBrands()
    setBrands(data)
  }

  useEffect(() => {
    let alive = true
    async function boot() {
      setLoading(true)
      setError(null)
      try {
        await loadBrands()

        if (isEdit && id != null) {
          const truck = await getTruck(id)
          if (!alive) return

          // Melhor esforço: mapear o nome do backend para o code da FIPE.
          // Se não encontrar, mantemos o nome (o backend aceita por nome também).
          setForm((s) => ({
            ...s,
            license_plate: truck.license_plate,
            brand: truck.brand,
            model: truck.model,
            manufacturing_year: String(truck.manufacturing_year),
          }))
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Erro ao inicializar formulário.')
      } finally {
        setLoading(false)
      }
    }
    void boot()
    return () => {
      alive = false
    }
  }, [id, isEdit])

  // Quando escolhe marca: carrega modelos e limpa dependências
  useEffect(() => {
    if (!form.brand) {
      setModels([])
      setYears([])
      return
    }

    // Se form.brand não é code, tenta converter pra code
    const brandCodeOrName = selectedBrand?.code ?? form.brand
    void (async () => {
      try {
        const data = await fipeModels(brandCodeOrName)
        setModels(data)
      } catch (e) {
        setModels([])
        setYears([])
        setError(e instanceof Error ? e.message : 'Erro ao carregar modelos.')
      }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.brand])

  // Quando escolhe modelo: carrega anos e limpa dependências
  useEffect(() => {
    if (!form.brand || !form.model) {
      setYears([])
      return
    }
    const brandCodeOrName = selectedBrand?.code ?? form.brand
    const modelCodeOrName = selectedModel?.code ?? form.model
    void (async () => {
      try {
        const data = await fipeYears(brandCodeOrName, modelCodeOrName)
        setYears(data)
      } catch (e) {
        setYears([])
        setError(e instanceof Error ? e.message : 'Erro ao carregar anos.')
      }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.model, form.brand])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setTouched({ license_plate: true, brand: true, model: true, manufacturing_year: true })
    setError(null)
    setSuccess(null)

    if (!canSubmit) return

    const brandName = selectedBrand?.name ?? form.brand
    const modelName = selectedModel?.name ?? form.model

    const year =
      selectedYear ? parseYearFromLabel(selectedYear.name) : parseYearFromLabel(form.manufacturing_year)
    const yearNumber = year ?? Number(form.manufacturing_year)
    if (!Number.isFinite(yearNumber)) {
      setError('Ano inválido.')
      return
    }

    setSubmitting(true)
    try {
      if (isEdit && id != null) {
        await updateTruck(id, {
          brand: brandName,
          model: modelName,
          manufacturing_year: yearNumber,
        })
        setSuccess('Caminhão atualizado com sucesso.')
        setTimeout(() => nav('/'), 400)
      } else {
        await createTruck({
          license_plate: normalizePlate(form.license_plate),
          brand: brandName,
          model: modelName,
          manufacturing_year: yearNumber,
        })
        setSuccess('Caminhão cadastrado com sucesso.')
        setTimeout(() => nav('/'), 400)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar.')
    } finally {
      setSubmitting(false)
    }
  }

  // Quando inicializa em modo edição: tenta selecionar codes após brands/models carregarem
  useEffect(() => {
    if (!isEdit) return
    if (!form.brand) return
    if (brands.length === 0) return
    const match = brands.find((b) => b.name.toLowerCase() === form.brand.toLowerCase())
    if (match && match.code !== form.brand) {
      setField('brand', match.code)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brands.length])

  useEffect(() => {
    if (!isEdit) return
    if (!form.brand || !form.model) return
    if (models.length === 0) return
    const currentModelName = typeof form.model === 'string' ? form.model : ''
    const match = models.find((m) => m.name.toLowerCase() === currentModelName.toLowerCase())
    if (match && match.code !== form.model) {
      setField('model', match.code)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [models.length])

  useEffect(() => {
    if (!isEdit) return
    if (!form.manufacturing_year) return
    if (years.length === 0) return
    const yearNum = Number(form.manufacturing_year)
    const match = years.find((y) => parseYearFromLabel(y.name) === yearNum)
    if (match && match.code !== form.manufacturing_year) {
      setField('manufacturing_year', match.code)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [years.length])

  return (
    <div className="card">
      <div className="titleRow">
        <h1>{isEdit ? 'Atualizar caminhão' : 'Cadastrar caminhão'}</h1>
        <Link className="btn" to="/">
          Voltar
        </Link>
      </div>

      {error && <div className="alert alertError">{error}</div>}
      {success && <div className="alert alertSuccess">{success}</div>}

      {loading ? (
        <div className="badge">Carregando...</div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="formGrid">
            <div className="field">
              <label>Placa</label>
              <input
                value={form.license_plate}
                onChange={(e) => setField('license_plate', e.target.value)}
                onBlur={() => setTouched((t) => ({ ...t, license_plate: true }))}
                placeholder="AAA-1234 ou AAA1A23"
                disabled={isEdit}
              />
              {fieldError('license_plate') && <div className="fieldError">{fieldError('license_plate')}</div>}
            </div>

            <div className="field">
              <label>Marca (FIPE)</label>
              <select
                value={form.brand}
                onChange={(e) => {
                  setField('brand', e.target.value)
                  setField('model', '')
                  setField('manufacturing_year', '')
                  setTouched((t) => ({ ...t, brand: true }))
                }}
                onBlur={() => setTouched((t) => ({ ...t, brand: true }))}
              >
                <option value="">Selecione...</option>
                {brands.map((b) => (
                  <option key={b.code} value={b.code}>
                    {b.name}
                  </option>
                ))}
              </select>
              {fieldError('brand') && <div className="fieldError">{fieldError('brand')}</div>}
            </div>

            <div className="field">
              <label>Modelo (FIPE)</label>
              <select
                value={form.model}
                onChange={(e) => {
                  setField('model', e.target.value)
                  setField('manufacturing_year', '')
                  setTouched((t) => ({ ...t, model: true }))
                }}
                onBlur={() => setTouched((t) => ({ ...t, model: true }))}
                disabled={!form.brand || models.length === 0}
              >
                <option value="">Selecione...</option>
                {models.map((m) => (
                  <option key={m.code} value={m.code}>
                    {m.name}
                  </option>
                ))}
              </select>
              {fieldError('model') && <div className="fieldError">{fieldError('model')}</div>}
            </div>

            <div className="field">
              <label>Ano (FIPE)</label>
              <select
                value={form.manufacturing_year}
                onChange={(e) => {
                  setField('manufacturing_year', e.target.value)
                  setTouched((t) => ({ ...t, manufacturing_year: true }))
                }}
                onBlur={() => setTouched((t) => ({ ...t, manufacturing_year: true }))}
                disabled={!form.brand || !form.model || years.length === 0}
              >
                <option value="">Selecione...</option>
                {years.map((y) => (
                  <option key={y.code} value={y.code}>
                    {y.name}
                  </option>
                ))}
              </select>
              {fieldError('manufacturing_year') && (
                <div className="fieldError">{fieldError('manufacturing_year')}</div>
              )}
            </div>
          </div>

          <div className="actionsRow">
            <Link className="btn" to="/">
              Cancelar
            </Link>
            <button className="btn btnPrimary" type="submit" disabled={!canSubmit || submitting}>
              {submitting ? 'Salvando...' : isEdit ? 'Atualizar' : 'Cadastrar'}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

