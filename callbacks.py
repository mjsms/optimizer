# optimizer/callbacks.py
from pymoo.core.callback import Callback
from pymoo.performance_indicator.hv import HV
import numpy as np, json, time, pathlib

class TraceCallback(Callback):
    def __init__(self, ref_point):
        super().__init__()
        self.hv   = HV(ref_point)
        self.file = pathlib.Path("/mnt/data/run_trace.jsonl")  # 1 linha por gen.

    def notify(self, algorithm):
        F = algorithm.pop.get("F")            # matriz N×m métricas
        hv  = float(self.hv(F))
        gen = int(algorithm.n_gen)
        best = F.min(axis=0).tolist()         # melhor de cada objectivo
        logline = json.dumps(
            {"t": time.time(), "gen": gen, "hv": hv, "best": best})
        self.file.write_text(logline + "\n", append=True)
