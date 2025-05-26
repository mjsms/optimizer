# optimiser/callbacks.py
from pathlib import Path
import json, time
import numpy as np
from pymoo.core.callback import Callback
from pymoo.indicators.hv import HV


class TraceCallback(Callback):
    """
    Guarda, em JSON-Lines, a evolução da fronha de Pareto
    (hyper-volume + melhor valor de cada objectivo).
    """

    def __init__(self, ref_point):
        super().__init__()
        self.hv   = HV(ref_point)
        self.file = Path("run_trace.jsonl")        # 1 linha por geração
        # limpa ficheiro anterior
        if self.file.exists():
            self.file.unlink()

    # --------------------------------------------------------------
    def notify(self, algorithm):
        F   = algorithm.pop.get("F")               # matriz NxM (métricas)
        hv  = float(self.hv(F))
        gen = int(algorithm.n_gen)
        best = F.min(axis=0).tolist()              # melhor por objectivo

        logline = json.dumps({"t": time.time(),
                              "gen": gen,
                              "hv": hv,
                              "best": best})

        # append seguro
        with self.file.open("a", encoding="utf-8") as fp:
            fp.write(logline + "\n")
