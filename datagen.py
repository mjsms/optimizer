import json, random, itertools, pathlib, datetime as dt

# ----- parâmetros rápidos -----
N_CLASSES = 10
WEEKDAYS  = list(range(5))          # 0=Seg … 4=Sex
START_HRS = [8, 9.5, 11, 14]        # horas de início possíveis
DURATION  = 1.5                     # duração (h)

# ----- gera aulas -----
classes = [
    {
        "id": i,
        "name": f"UC_{i:02d}",
        "students": random.randint(15, 45)
    }
    for i in range(N_CLASSES)
]

# ----- gera slots (dia, idx) -----
slots  = []
slot_id = 0
for wd, hr in itertools.product(WEEKDAYS, START_HRS):
    start = dt.time(int(hr), int((hr % 1) * 60)).strftime("%H:%M")
    end   = (dt.datetime.combine(dt.date.today(), dt.time()) +
             dt.timedelta(hours=hr + DURATION)).time()
    slots.append({
        "id": slot_id,
        "weekday": wd,
        "start": start,
        "end":   end.strftime("%H:%M")
    })
    slot_id += 1

# (opcional) salas muito simples
rooms = [
    {"id": 0, "name": "A1", "capacity": 40},
    {"id": 1, "name": "B1", "capacity": 30},
]

payload = {"data": {"classes": classes, "slots": slots, "rooms": rooms}}

# grava para ficheiro
out_path = pathlib.Path("sample_payload.json")
out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
print(f"Ficheiro gerado em {out_path}")
