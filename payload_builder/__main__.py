# datagen/datagen.py  (GUID + chamada API)
import csv, json, random, itertools, pathlib, datetime as dt, uuid, requests

BASE_DIR = pathlib.Path(__file__).parent
OUT_DIR  = BASE_DIR / "payloads";  OUT_DIR.mkdir(exist_ok=True)
API_URL  = "http://localhost:8000/optimise"       # <- ajusta

# -------------------------- CSV -> classes ---------------------------------
def read_csv(path, encodings=("utf-8-sig", "latin-1")):
    for enc in encodings:
        try:
            return csv.DictReader(path.open(encoding=enc, newline=""))
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"impossível ler {path}")

subjects = []
for row in read_csv(BASE_DIR / "subjects.csv"):
    try:
        subjects.append((
            int(row["id"]),
            row["name"].strip('" '),
            int(row.get("students") or row.get("academicProgramId"))
        ))
    except (KeyError, ValueError):
        continue

rooms = []
for row in read_csv(BASE_DIR / "rooms.csv"):
    try:
        rooms.append({
            "id":        int(row["id"]),
            "name":      row["name"].strip('" '),
            "capacity":  int(row["capacity"]),
            "features":  [f.strip() for f in row.get("features","").split(";") if f.strip()]
        })
    except (KeyError, ValueError):
        continue

YEARS = (1, 2, 3)
classes = [{
    "id": sid,
    "name": name,
    "size": size,
    "year": random.choice(YEARS),
    "duration": random.choice([1, 2]),
    "reqFeatures": ["Lab"] if random.random() < .25 else []
} for sid, name, size in subjects]

# -------------------------- slots gerados ----------------------------------
WEEKDAYS, START_HRS, BLOCK = range(5), [8, 9.5, 11, 14, 15.5, 17], 1.5
slots, sid = [], 0
for wd, hr in itertools.product(WEEKDAYS, START_HRS):
    h, m = divmod(int(hr * 60), 60)
    start = dt.time(h, m).strftime("%H:%M")
    end   = (dt.datetime.combine(dt.date.today(), dt.time(h, m))
             + dt.timedelta(hours=BLOCK)).time().strftime("%H:%M")
    slots.append({"id": sid, "weekday": wd, "start": start, "end": end})
    sid += 1

payload = {"data": {"classes": classes, "slots": slots, "rooms": rooms}}

# -------------------------- GUID, gravação e API ---------------------------
guid = uuid.uuid4().hex          # sem hífens
payload_file  = OUT_DIR / f"payload_{guid}.json"
response_file = OUT_DIR / f"response_{guid}.json"

payload_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                        encoding="utf-8")
print(f"✔  Payload gravado    -> {payload_file.name}")

try:
    resp = requests.post(API_URL, json=payload, timeout=99999)
    resp.raise_for_status()
    response_file.write_text(resp.text, encoding="utf-8")
    print(f"✔  Resposta da API    -> {response_file.name} "
          f"({len(resp.json().get('pareto',[]))} soluções)")
except requests.RequestException as e:
    print(f"❌  Falha na chamada à API: {e}")
