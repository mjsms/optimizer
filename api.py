# optimiser/api.py
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.indicators.hv import HV

from model import TimetableProblem
from callbacks import TraceCallback

app = FastAPI(title="ISCTE Timetable Optimiser")


# ---------- schemas ---------- #
class OptimiseIn(BaseModel):
    data: dict
    pop_size: int = 400 #valores default, caso nenhum seja passado
    n_gen:    int = 100


class SolutionOut(BaseModel):
    id:         int
    allocation: list
    metrics:    dict


class OptimiseOut(BaseModel):
    pareto: list[SolutionOut]
    hv: float


# ---------- helpers ---------- #
def decode_allocation(problem: TimetableProblem, X):
    """Converte um vector numpy -> lista de alocações legível."""
    return problem._decode(X.tolist())


# ---------- endpoint ---------- #
@app.post("/optimise", response_model=OptimiseOut)
def optimise(body: OptimiseIn):
    """
    Recebe `body.data` = payload JSON  ➜  devolve soluções não-dominadas.
    """
    payload = body.data.get("data", body.data)   # aceitar `{data:{...}}` ou só `{...}`

    # 1) problema + algoritmo
    prob = TimetableProblem(payload)
    algo = NSGA2(pop_size=body.pop_size)

    # 2) ponto de referência para HV (ajuste conforme seu domínio de valores)
    ref_point = np.array([3000.0, 1000.0])

    # 3) callback (opcional)
    cb = TraceCallback(ref_point=ref_point)

    # 4) optimizar
    res = minimize(prob, algo, ('n_gen', body.n_gen),
                   callback=cb, verbose=False)

    # 5) construir Pareto
    pareto = [
        {
            "id": i,
            "allocation": decode_allocation(prob, res.X[i]),
            "metrics": {
                "conflicts": int(res.F[i, 0]),
                "waste":     int(res.F[i, 1]),
            },
        }
        for i in range(len(res.F))
    ]

    # 6) calcular o Hyper‐Volume
    hv_indicator = HV(ref_point)
    hv_value = float(hv_indicator(res.F))

    return {"pareto": pareto, "hv": hv_value}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="localhost", port=8000, reload=True)
