# optimiser/api.py
from fastapi import FastAPI
from pydantic import BaseModel
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize

from model import TimetableProblem
from callbacks import TraceCallback

app = FastAPI(title="ISCTE Timetable Optimiser")


# ---------- schemas ---------- #
class OptimiseIn(BaseModel):
    data: dict
    pop_size: int = 400
    n_gen:    int = 200


class SolutionOut(BaseModel):
    id:         int
    allocation: list           # [{class_id, slot_id, room_id}, …]
    metrics:    dict           # conflicts / crowding / gaps


class OptimiseOut(BaseModel):
    pareto: list[SolutionOut]


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

    # 2) callback (opcional)
    cb = TraceCallback(ref_point=[2000, 20000])

    # 3) optimizar
    res = minimize(prob, algo, ('n_gen', body.n_gen),
                   callback=cb, verbose=False)

    # 4) construir Pareto
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

    return {"pareto": pareto}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
