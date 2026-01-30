import './App.css'
import { Link, Navigate, Route, Routes } from 'react-router-dom'

import { ListTrucks } from './pages/ListTrucks'
import { TruckForm } from './pages/TruckForm'

function App() {
  return (
    <>
      <header className="topbar">
        <div className="topbarInner">
          <div className="brand">AgroFrota</div>
          <nav className="nav">
            <Link className="btn" to="/">
              Listagem
            </Link>
            <Link className="btn btnPrimary" to="/new">
              Cadastrar
            </Link>
          </nav>
        </div>
      </header>

      <main className="container">
        <Routes>
          <Route path="/" element={<ListTrucks />} />
          <Route path="/new" element={<TruckForm />} />
          <Route path="/edit/:id" element={<TruckForm />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  )
}

export default App
