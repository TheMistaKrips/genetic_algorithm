import json
import pandas as pd

INPUT_JSON = "exam_list.json"
INPUT_CSV  = "extracted_data_v3.csv"
OUTPUT_JSON = "exam_list_clean.json"

# ---------- 0. Проверка: есть ли 4-ИК в исходных данных? ----------
df = pd.read_csv(INPUT_CSV, sep=';')
has_4ik = (
    (df['Лист'].astype(str).str.startswith('4'))
    & (df['Специальность'].astype(str).str.startswith('11.03.02'))
).any()
print(f"[проверка] 4-ИК в CSV: {'ДА' if has_4ik else 'НЕТ (значит, у группы нет пар в этом семестре)'}")

# ---------- Загрузка ----------
with open(INPUT_JSON, encoding='utf-8') as f:
    exams = json.load(f)
print(f"[вход] Экзаменов: {len(exams)}")

# ---------- 1. Удалить «Учебная ...» (практики) ----------
before = len(exams)
exams = [e for e in exams if not e['subject'].startswith('Учебная')]
print(f"[1] Удалено практик: {before - len(exams)}")

# ---------- 2. «Не указан» → уникальный Unknown_N ----------
cnt_unknown = 0
for e in exams:
    new_teachers = []
    for t in e['teachers']:
        if t == 'Не указан':
            new_teachers.append(f"Unknown_{e['id']}")
            cnt_unknown += 1
        else:
            new_teachers.append(t)
    e['teachers'] = new_teachers
print(f"[2] Заменено 'Не указан' → Unknown_N: {cnt_unknown}")

# ---------- 3. Аудитория «?» → «TBD» ----------
cnt_tbd = 0
for e in exams:
    if e['room'] == '?':
        e['room'] = 'TBD'
        cnt_tbd += 1
print(f"[3] Заменено room '?' → TBD: {cnt_tbd}")

# ---------- 4. Опечатка «Искуственный» → «Искусственный» ----------
for e in exams:
    if e['subject'] == 'Искуственный интелект':
        e['subject'] = 'Искусственный интеллект'
        print("[4] Исправлена опечатка: Искуственный → Искусственный")

# ---------- 5. Объединить «Базы данных» (Каратаева П.М.) ----------
bd = [e for e in exams
      if e['subject'] == 'Базы данных' and e['teachers'] == ['Каратаева П.М.']]
if len(bd) > 1:
    all_groups = sorted({g for e in bd for g in e['groups']})
    merged = {
        'subject':  'Базы данных',
        'teachers': ['Каратаева П.М.'],
        'groups':   all_groups,
        'room':     '225',        # лекционная из расписания
        'capacity': 50,
        'is_online': False,
        'id':       bd[0]['id'],
    }
    bd_ids = {e['id'] for e in bd}
    exams = [e for e in exams if e['id'] not in bd_ids] + [merged]
    print(f"[5] Объединено 'Базы данных': {len(bd)} → 1 экзамен, группы={all_groups}")

# ---------- Перенумеровать ID ----------
for i, e in enumerate(exams, 1):
    e['id'] = i

# ---------- Сохранение ----------
with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(exams, f, ensure_ascii=False, indent=2)
print(f"\n✅ Готово! Экзаменов: {len(exams)} → {OUTPUT_JSON}")

# ---------- Краткая сводка ----------
online = sum(1 for e in exams if e['is_online'])
print(f"   Онлайн: {online}, оффлайн: {len(exams) - online}")

groups_count = {}
for e in exams:
    for g in e['groups']:
        groups_count[g] = groups_count.get(g, 0) + 1
print(f"\n   Экзаменов на группу:")
for g in sorted(groups_count):
    print(f"     {g}: {groups_count[g]}")

missing_teachers = [e['id'] for e in exams if any(t.startswith('Unknown_') for t in e['teachers'])]
if missing_teachers:
    print(f"\n   Экзамены с Unknown_N: {missing_teachers}")