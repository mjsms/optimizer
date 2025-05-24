# optimiser/model.py
class TimetableProblem(Problem):

    def __init__(self, data):
        self.data = data              # guarda payload
        n    = len(data["classes"])
        xl   = np.zeros(n, dtype=int)           # slotId min
        xu   = np.full (n, len(data["slots"])-1)  # slotId max
        super().__init__(n_var=n, n_obj=2, xl=xl, xu=xu)

    # ---------- decodifica vector ---------- #
    def _decode(self, X):
        # X é vector slotIds
        timetable = []
        for gene, klass in zip(X, self.data["classes"]):
            timetable.append({
                "class_id": klass["id"],
                "slot_id": int(gene),
                # se também optimizas sala: "room_id": gene % nRooms
            })
        return timetable

    # ---------- avalia ---------- #
    def _evaluate(self, X, out, *args, **kwargs):
        timetable = self._decode(X)
        f1_conflicts = 0
        f2_waste     = 0

        # índices rápidos
        slotByProf = {}
        slotByYear = {}
        occ        = set()     # (slot, room)

        for row in timetable:
            klass   = next(c for c in self.data["classes"]
                             if c["id"] == row["class_id"])
            slot    = row["slot_id"]
            roomId  = row.get("room_id") or klass.get("preferredRoom")

            # --- conflito de professor ---
            # key_prof = (klass["prof"], slot)
            # if key_prof in slot_by_prof:
            #     f1_conflicts += 1
            # slot_by_prof[key_prof] = True


            keyYear = (klass["year"], slot)
            if keyYear in slotByYear:   f1_conflicts += 1
            slotByYear[keyYear] = True

            if (slot, roomId) in occ:   f1_conflicts += 1
            occ.add((slot, roomId))

            # --- capacidade ---
            room = next(r for r in self.data["rooms"] if r["id"] == roomId)
            if klass["size"] > room["capacity"]:
                f1_conflicts += 1
            else:
                f2_waste += room["capacity"] - klass["size"]

        out["F"] = [f1_conflicts, f2_waste]
