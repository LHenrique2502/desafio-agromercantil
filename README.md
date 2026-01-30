# Desafio AgroMercantil — Frota de Caminhões (Django + React)

Aplicação completa (**API + Interface Web**) para cadastro, listagem e atualização de caminhões, com **validação e precificação via FIPE**.

## Requisitos

- **Python 3.12+**
- **Node 20.x** (recomendado 20.19+; funciona com 20.16 ajustando Vite para v5)

## Como rodar (sem Docker)

### Backend (Django + DRF)

```bash
cd backend
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

API em `http://127.0.0.1:8000/api/`

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Front em `http://127.0.0.1:5173/`

> O Vite está configurado com proxy para `/api` apontando para `http://127.0.0.1:8000` em [`frontend/vite.config.ts`](frontend/vite.config.ts).

## Endpoints

### Caminhões

- **POST** `/api/trucks/` — cadastrar caminhão  
  - Regra: **placa única** (não permite duplicar)
  - Validação FIPE: marca/modelo/ano precisam existir na FIPE
  - `fipe_price` é calculado e persistido

- **GET** `/api/trucks/` — listar caminhões

- **PATCH** `/api/trucks/{id}/` — atualizar caminhão  
  - Permite atualizar **apenas** `brand`, `model`, `manufacturing_year`
  - Revalida FIPE e recalcula `fipe_price`

### FIPE (via backend)

- **GET** `/api/fipe/brands/`
- **GET** `/api/fipe/models/?brand=<code_ou_nome>`
- **GET** `/api/fipe/years/?brand=<code_ou_nome>&model=<code_ou_nome>`

## Exemplos (curl)

### Criar

```bash
curl -X POST http://127.0.0.1:8000/api/trucks/ ^
  -H "Content-Type: application/json" ^
  -d "{\"license_plate\":\"ABC1D23\",\"brand\":\"AGRALE\",\"model\":\"10000 / 10000 S  2p (diesel) (E5)\",\"manufacturing_year\":2022}"
```

### Listar

```bash
curl http://127.0.0.1:8000/api/trucks/
```

### Atualizar

```bash
curl -X PATCH http://127.0.0.1:8000/api/trucks/1/ ^
  -H "Content-Type: application/json" ^
  -d "{\"brand\":\"AGRALE\",\"model\":\"10000 / 10000 S  2p (diesel) (E5)\",\"manufacturing_year\":2022}"
```

## Testes

### Backend

Os testes **mockam a FIPE** (não dependem de internet).

```bash
cd backend
python manage.py test
```
