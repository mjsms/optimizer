import numpy as np
from pymoo.core.problem import Problem


class TimetableProblem(Problem):
    """
    F1 – Conflitos   (restrições 1-4)  · minimizar
    F2 – Qualidade   (restrições 5-7)  · minimizar
    """

    # ───────────────────────── constructor ──────────────────────────
    def __init__(self, data: dict):

        self.payload = data
        self.classes = data["classes"]
        self.rooms = data["rooms"]
        self.slots = data["slots"]

        self.n_rooms = len(self.rooms)
        self.n_slots = len(self.slots)

        super().__init__(
            n_var=len(self.classes),
            n_obj=2,
            xl=0,
            xu=self.n_rooms * self.n_slots - 1,
            type_var=np.int64
        )

        # --------- pré-cálculo de arrays para acesso O(1) ----------
        self.room_cap = np.asarray([r["capacity"] for r in self.rooms], dtype=np.int64)
        self.size = np.asarray([c["size"] for c in self.classes], dtype=np.int64)
        self.year = np.asarray([c["year"] for c in self.classes], dtype=np.int64)
        self.uc_id = np.asarray([c["id"] for c in self.classes], dtype=np.int64)

        self.slot_weekday = np.asarray([s["weekday"] for s in self.slots], dtype=np.int64)
        self.slots_per_day = int(np.sum(self.slot_weekday == self.slot_weekday[0]))

        self.room_by_idx = {i: r for i, r in enumerate(self.payload["rooms"])}
        self.room_by_id = {r["id"]: r for r in self.payload["rooms"]}

        # slots de almoço (começam às 12 h)
        self.lunch_ids = {i for i, s in enumerate(self.slots)
                          if str(s["start"]).startswith("12")}

    # ───────────────────── helper opcional: gaps ────────────────────
    def _calc_gaps(self, slot_vec: np.ndarray) -> int:
        """Conta horas vazias (‘gaps’) entre aulas do mesmo ano no mesmo dia."""
        gaps = 0
        for yr in np.unique(self.year):
            idx = np.where(self.year == yr)[0]
            if idx.size < 2:
                continue
            sl_y = slot_vec[idx]
            wd = self.slot_weekday[sl_y]
            pos_d = sl_y % self.slots_per_day
            for d in np.unique(wd):
                s = np.sort(pos_d[wd == d])
                gaps += int(np.sum(s[1:] - s[:-1] - 1))  # restrição 7
        return gaps

    # ───────────────────────── avaliação ────────────────────────────
    def _evaluate(self, X, out, *args, **kwargs):
        """
        X shape = (pop, n_var).  Preenche out["F"] shape = (pop, 2)
        """

        X = X.astype(np.int64, copy=False)
        slot = X // self.n_rooms  # posição temporal
        room = X % self.n_rooms  # sala atribuída

        # ========== F1  (conflitos) ==================================
        # restrição 1 – capacidade insuficiente
        cap_violation = (self.size > self.room_cap[room]).sum(axis=1)

        # restrição 2 – duas turmas na mesma (slot, sala)
        same_room = X.shape[1] - np.apply_along_axis(
            lambda r: np.unique((slot[r] * 10_000 + room[r])).size, 1,
            np.arange(X.shape[0])[:, None])

        # restrição 3 – duas turmas do mesmo ano no mesmo slot
        same_year = X.shape[1] - np.apply_along_axis(
            lambda r: np.unique((slot[r] * 10_000 + self.year[r])).size, 1,
            np.arange(X.shape[0])[:, None])

        # restrição 4 – aula em slot de almoço
        lunch_conf = np.isin(slot, list(self.lunch_ids)).sum(axis=1)

        f1 = cap_violation + same_room + same_year + lunch_conf

        # ========== F2  (qualidade) ==================================
        # restrição 5 – waste normalizado
        free = np.maximum(self.room_cap[room] - self.size, 0)  # nunca negativo
        waste = (free / self.room_cap[room]).sum(axis=1)

        # restrição 6 – aulas da mesma UC concentradas num único dia
        day = self.slot_weekday[slot]
        uc_same_day = X.shape[1] - np.apply_along_axis(
            lambda r: np.unique(self.uc_id[r] * 10 + day[r]).size, 1,
            np.arange(X.shape[0])[:, None])

        # restrição 7 – gaps
        gaps = np.array([self._calc_gaps(ind_slot)  # ind_slot = slot[i]
                        for ind_slot in slot],
                        dtype = np.int64)

        f2 = waste + uc_same_day + gaps

        out["F"] = np.column_stack([f1, f2])  # shape (pop, 2)

    # ───────────────────────── decode ───────────────────────────────
    def _decode(self, X):
        """
        Converte vector numpy -> lista de dicionários legível pela API.
        """
        timetable = []
        for gene, klass in zip(X, self.payload["classes"]):
            slot_idx = int(gene) // self.n_rooms
            room_idx = int(gene) % self.n_rooms
            room_id = self.room_by_idx[room_idx]["id"]

            timetable.append({
                "class_id": klass["id"],
                "slot_id": slot_idx,
                "room_id": room_id,
            })
        return timetable
