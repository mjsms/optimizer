# optimiser/model.py
from pymoo.core.problem import ElementwiseProblem
import numpy as np

class TimetableProblem(ElementwiseProblem):
    """
    Cada gene codifica (slot , sala):

        gene = slot_idx * n_rooms + room_idx
    """

    # ------------------------------------------------------------------
    def __init__(self, data: dict):
        self.payload  = data                      # guarda payload
        self.n_slots  = len(data["slots"])
        self.n_rooms  = len(data["rooms"])
        n_vars        = len(data["classes"])

        xl = np.zeros(n_vars, dtype=int)
        xu = np.full (n_vars, self.n_slots * self.n_rooms - 1)

        super().__init__(n_var=n_vars, n_obj=2, xl=xl, xu=xu)

        # lookup rápido de salas
        self.room_by_idx = {i: r for i, r in enumerate(self.payload["rooms"])}
        self.room_by_id  = {r["id"]: r for r in self.payload["rooms"]}
        
        # número de slots por dia (assumindo distribuição uniforme)
        self.slots_per_day = len(data["slots"]) // 6  # assumindo 5 dias úteis + sábado

    # ------------------------------------------------------------------
    def _get_day_from_slot(self, slot_idx):
        """
        Converte um slot_idx para o dia correspondente (0-4 para seg-sex).
        """
        return slot_idx // self.slots_per_day

    # ------------------------------------------------------------------
    def _decode(self, X):
        """
        Converte vector numpy -> lista de dicionários legível pela API.
        """
        timetable = []
        for gene, klass in zip(X, self.payload["classes"]):

            slot_idx  = int(gene) // self.n_rooms
            room_idx  = int(gene) %  self.n_rooms
            room_id   = self.room_by_idx[room_idx]["id"]

            timetable.append({
                "class_id": klass["id"],
                "slot_id":  slot_idx,
                "room_id":  room_id,
            })
        return timetable

    # ------------------------------------------------------------------
    def _evaluate(self, X, out, *args, **kwargs):
        """
        F1  = nº de conflitos (salas sobre-lotadas, turmas a sobrepor-se …)
        F2  = desperdício de capacidade (quanto > pior)
        """
        timetable   = self._decode(X)
        f1_conflict = 0
        f2_waste    = 0

        slot_by_year = {}
        occ          = set()               # (slot, room)

        classes_per_day = {}      # {day: count}
        class_days = {}          # {class_id: set(days)}

        for row in timetable:
            klass   = next(c for c in self.payload["classes"]
                            if c["id"] == row["class_id"])
            slot    = row["slot_id"]
            room_id = row["room_id"]
            day     = self._get_day_from_slot(slot)

            # restrição 2) capacidade da sala
            room = self.room_by_id[room_id]
            if klass["size"] > room["capacity"]:
                f1_conflict += 1
            else:
                f2_waste += room["capacity"] - klass["size"]

            # restrição 4) duas turmas do mesmo ano no mesmo slot
            key = (klass["year"], slot)
            if key in slot_by_year:
                f1_conflict += 1
            slot_by_year[key] = True

            # restrição 5) colidir duas turmas na mesma sala
            if (slot, room_id) in occ:
                f1_conflict += 1
            occ.add((slot, room_id))

            # restriçao 6) Máximo 3 aulas da mesma UC por dia
            classes_per_day[day] = classes_per_day.get(day, 0) + 1
            if classes_per_day[day] > 3:
                f1_conflict += 1

            # restriçao 7) Distribuição de aulas da UC ao longo da semana
            if klass["id"] not in class_days:
                class_days[klass["id"]] = set()
            if day in class_days[klass["id"]]:
                f1_conflict += 1
            class_days[klass["id"]].add(day)

        out["F"] = [f1_conflict, f2_waste]
