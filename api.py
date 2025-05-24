# optimiser/api.py
from fastapi import FastAPI
from pydantic import BaseModel
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize

from model import TimetableProblem, decode
from callbacks import TraceCallback

app = FastAPI(title="ISCTE Timetable Optimiser")

# ---------- schema de entrada/saída ----------
class OptimiseIn(BaseModel):
    data: dict                      # payload com classes, rooms, slots
    pop_size: int = 200
    n_gen:    int = 400

class SolutionOut(BaseModel):
    id:        int
    allocation: list                # vector class_id / slot / room
    metrics:   dict                 # conflicts, crowding, gaps

class OptimiseOut(BaseModel):
    pareto: list[SolutionOut]

# ---------- endpoint ----------
@app.post("/optimise", response_model=OptimiseOut)
def optimise(body: OptimiseIn):
    """
    Recebe `body.data` = payload JSON,
    devolve lista de soluções não-dominadas.
    """

    # 1) instanciar problema e algoritmo
    prob = TimetableProblem(body.data)
    algo = NSGA2(pop_size=body.pop_size)

    # 2) callback p/ log (opcional)
    cb = TraceCallback(ref_point=[50, 100, 40])

    # 3) correr optimizador
    res = minimize(prob, algo, ('n_gen', body.n_gen),
                   callback=cb, verbose=False)

    # 4) construir Pareto para resposta
    pareto = [
        {
            "id": i,
            "allocation": decode(res.X[i], body.data),
            "metrics": {
                "conflicts": int(res.F[i, 0]),
                "crowding":  int(res.F[i, 1]),
                "gaps":      int(res.F[i, 2]),
            },
        }
        for i in range(len(res.F))
    ]

    return {"pareto": pareto}
