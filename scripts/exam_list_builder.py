import pandas as pd
import re
import json

# ============ КОНФИГУРАЦИЯ ============
INPUT_CSV = "extracted_data_v3.csv"
OUTPUT_JSON = "exam_list.json"

IT_SPECIALTIES = {"09.03.02", "11.03.02", "10.03.01"}
SPECIALTY_SHORT = {"09.03.02": "ИС", "11.03.02": "ИК", "10.03.01": "ИБ"}

BIG_ROOMS = {"227", "229", "301", "101"}
DEFAULT_CAPACITY = 25
BIG_CAPACITY = 50
ONLINE_CAPACITY = 999
STUDENTS_PER_GROUP = 20   # настраивается

EXCLUDE_KEYWORDS = ["элективные курсы", "физическая культура"]
# =====================================


def clean_subject(s):
    if not s: return ""
    s = str(s)
    s = re.sub(r'^[\s\-\.\\,]+', '', s)
    date_pattern = r'^\d{1,2}\.\d{2}(?:\.\d{2})?(?:\s*[-+]\s*\d{1,2}\.\d{2}(?:\.\d{2})?)?(?:[,\s]+\d{1,2}\.\d{2}(?:\.\d{2})?)*\s*'
    while re.match(date_pattern, s):
        s = re.sub(date_pattern, '', s, count=1)
        s = re.sub(r'^[\s\-\.\\,]+', '', s)
    return s.strip(' .,-;')


def should_exclude(subject):
    if not subject or len(subject) < 3:
        return True
    low = subject.lower()
    for kw in EXCLUDE_KEYWORDS:
        if kw in low: return True
    if low.endswith("практика") or low.endswith("практикум"):
        return True
    return False


def extract_course(sheet):
    m = re.match(r'(\d+)', str(sheet))
    return int(m.group(1)) if m else 0


def extract_spec_code(spec):
    m = re.match(r'(\d+\.\d+\.\d+)', str(spec))
    return m.group(1) if m else None


def get_capacity(room, is_online):
    if is_online: return ONLINE_CAPACITY
    if not room or room in ('?', 'nan', 'None', ''): return DEFAULT_CAPACITY
    return BIG_CAPACITY if room in BIG_ROOMS else DEFAULT_CAPACITY


def split_groups(groups, capacity):
    if capacity >= ONLINE_CAPACITY:
        return [groups]
    max_per = max(1, capacity // STUDENTS_PER_GROUP)
    if max_per >= len(groups):
        return [groups]
    return [groups[i:i+max_per] for i in range(0, len(groups), max_per)]


def main():
    print(f"Загрузка {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV, sep=';')
    print(f"Всего строк: {len(df)}")

    df['spec_code'] = df['Специальность'].apply(extract_spec_code)
    df = df[df['spec_code'].isin(IT_SPECIALTIES)].copy()
    print(f"После фильтра IT: {len(df)}")

    df['course'] = df['Лист'].apply(extract_course)
    df = df[df['course'] > 0]
    df['group_id'] = df['course'].astype(str) + '-' + df['spec_code'].map(SPECIALTY_SHORT)
    print(f"Группы: {sorted(df['group_id'].unique())}")

    df['subject'] = df['Предмет'].apply(clean_subject)
    before = len(df)
    df = df[~df['subject'].apply(should_exclude)]
    print(f"После исключения физкультуры/практик: {len(df)} (-{before - len(df)})")

    df['is_online'] = df['Онлайн'] == 'Да'

    # Агрегация per (group, subject)
    rows = []
    for (gid, subj), sub in df.groupby(['group_id', 'subject']):
        teachers = set()
        offline_rooms = []
        all_online = True
        for _, r in sub.iterrows():
            for tn in str(r['Преподаватели']).split(';'):
                tn = tn.strip()
                if tn and tn not in ('Не указан', 'nan'):
                    teachers.add(tn)
            if not r['is_online']:
                all_online = False
                rm = str(r['Аудитория']).strip()
                if rm and rm not in ('?', 'nan', 'None', ''):
                    offline_rooms.append(rm)
        is_online = all_online
        if is_online:
            room = 'Online'
        else:
            big = [r for r in offline_rooms if r in BIG_ROOMS]
            room = big[0] if big else (offline_rooms[0] if offline_rooms else '?')
        rows.append({
            'group_id': gid, 'subject': subj,
            'teachers': tuple(sorted(teachers)) if teachers else ('Не указан',),
            'room': room, 'is_online': is_online,
        })
    per_group = pd.DataFrame(rows)
    print(f"Пар (группа, предмет): {len(per_group)}")

    # Объединение между группами
    final = []
    for (subj, teachers), grp in per_group.groupby(['subject', 'teachers']):
        groups = sorted(grp['group_id'].unique())
        is_online = bool(grp['is_online'].all())
        room = 'Online' if is_online else grp['room'].mode().iloc[0]
        capacity = get_capacity(room, is_online)
        for batch in split_groups(groups, capacity):
            final.append({
                'subject': subj, 'teachers': list(teachers),
                'groups': batch, 'room': room,
                'capacity': capacity, 'is_online': is_online,
            })

    for i, e in enumerate(final, 1):
        e['id'] = i

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Экзаменов: {len(final)} → {OUTPUT_JSON}")

    print("\n=== Экзаменов на группу ===")
    for g in sorted(set(g for e in final for g in e['groups'])):
        n = sum(1 for e in final if g in e['groups'])
        print(f"  {g}: {n}")

    print(f"\nОнлайн: {sum(1 for e in final if e['is_online'])}, оффлайн: {sum(1 for e in final if not e['is_online'])}")

    over = [e for e in final if not e['is_online'] and len(e['groups'])*STUDENTS_PER_GROUP > e['capacity']]
    print(f"\nПереполненных: {len(over)}")
    for e in over:
        print(f"  ⚠ #{e['id']} {e['subject']}: {len(e['groups'])}×{STUDENTS_PER_GROUP} > {e['capacity']}")

    print("\n=== 10 примеров ===")
    for e in final[:10]:
        print(f"  #{e['id']}: {e['subject']} | {', '.join(e['teachers'])} | ауд {e['room']} ({e['capacity']}) | гр: {e['groups']}")


if __name__ == '__main__':
    main()