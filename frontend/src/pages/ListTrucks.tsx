import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { listTrucks, type Truck } from '../services/api'

function formatPriceBRL(raw: string) {
  const n = Number(raw)
  if (Number.isFinite(n)) {
    return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  }
  return raw
}

export function ListTrucks() {
  const [items, setItems] = useState<Truck[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const count = useMemo(() => items.length, [items])

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await listTrucks()
      setItems(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar caminhões.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  return (
    <div className="card">
      <div className="titleRow">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <h1>Caminhões</h1>
          <span className="badge">{count} cadastrados</span>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn" onClick={() => void load()} disabled={loading}>
            Atualizar
          </button>
          <Link className="btn btnPrimary" to="/new">
            Cadastrar
          </Link>
        </div>
      </div>

      {error && <div className="alert alertError">{error}</div>}

      {loading ? (
        <div className="badge">Carregando...</div>
      ) : items.length === 0 ? (
        <div className="badge">Nenhum caminhão cadastrado ainda.</div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Placa</th>
              <th>Marca</th>
              <th>Modelo</th>
              <th>Ano</th>
              <th>Preço FIPE</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.id}>
                <td>{t.license_plate}</td>
                <td>{t.brand}</td>
                <td>{t.model}</td>
                <td>{t.manufacturing_year}</td>
                <td>{formatPriceBRL(t.fipe_price)}</td>
                <td style={{ textAlign: 'right' }}>
                  <Link className="btn" to={`/edit/${t.id}`}>
                    Editar
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

