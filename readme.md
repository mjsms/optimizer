
# ISCTE Timetable Optimiser 🗓️⚙️
Micro‑serviço em **Python 3.11 + FastAPI + pymoo** que gera horários não‑dominados
para o ISCTE recorrendo ao algoritmo **NSGA‑II**.

> Componente independente do sistema “Gestão de Horários”; comunica via
> HTTP / JSON com o backend Node.

---

## ✨ Funcionalidades

* **`POST /optimise`**
  * recebe dados de turmas, salas e _time‑slots_ em JSON
  * devolve a _frente de Pareto_ com métricas (`conflicts`, `crowding`, `gaps`)

* **TraceCallback** grava hyper‑volume por geração em ficheiro  
* Esquemas Pydantic ⇒ documentação Swagger automática  
* Pronto para correr em **docker‑compose**

---

## 📂 Estrutura

```text
optimiser/
├─ api.py            # FastAPI + endpoint /optimise
├─ model.py          # TimetableProblem (pymoo)
├─ callbacks.py      # TraceCallback (logging HV)
├─ datagen.py        # gera dados dummy para testes rápidos
├─ requirements.txt
└─ Dockerfile
```

---

## ⚡ Instalação rápida

```bash
git clone <repo> && cd optimiser
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# arrancar servidor
uvicorn api:app --reload --port 8000
```

* Swagger UI: <http://localhost:8000/docs>  
* Live‑reload activo com `--reload`.

---

## 🐋 Docker

```bash
docker build -t iscte-optimiser .
docker run -p 8000:8000 iscte-optimiser
```

`docker-compose.yml` de exemplo:

```yaml
services:
  optimiser:
    build: ./optimiser
    ports:
      - "8000:8000"
```

---

## 🔌 Especificação do endpoint

### Request

```jsonc
POST /optimise
Content-Type: application/json

{
  "data": {
    "classes": [
      {
        "id": 17,
        "size": 28,
        "prof": 4,
        "year": 1,
        "duration": 2,
        "reqFeatures": ["Lab"]
      }
    ],
    "rooms": [
      { "id": 12, "capacity": 40, "features": ["Lab", "Proj"] }
    ],
    "slots": [
      { "id": 0, "day": "Mon", "start": "08:00" }
    ]
  },
  "pop_size": 200,
  "n_gen": 400
}
```

### Response

```json
{
  "pareto": [
    {
      "id": 0,
      "allocation": [
        { "class_id": 17, "slot_id": 3, "room_id": 12 }
      ],
      "metrics": {
        "conflicts": 0,
        "crowding": 14,
        "gaps": 2
      }
    }
  ]
}
```

---

## 🔧 Personalização

| Onde                     | O quê                                                  |
|--------------------------|--------------------------------------------------------|
| `model.py`               | Fórmula de avaliação, número de objectivos, restrições |
| `callbacks.py`           | Ref‑point e formato de log (hyper‑volume)              |
| Corpo do `POST /optimise`| `pop_size`, `n_gen`, etc.                              |

---

## 🧪 Teste rápido

```bash
python - <<'PY'
from datagen import generate_dummy_payload
from api import optimise, OptimiseIn
resp = optimise(OptimiseIn(data=generate_dummy_payload()))
print(resp.json(indent=2))
PY
```

---

## 🗺️ Roadmap curto

* [ ] Permitir escolha de algoritmo (GA, PSO, …) via query‑param
* [ ] Exportar CSV/PDF da melhor solução
* [ ] Métrica de adequação de características da sala
* [ ] Persistir logs para análise offline

---

## 📜 Licença

MIT © 2024 – Mestrado em Engenharia Informática • ISCTE‑IUL
