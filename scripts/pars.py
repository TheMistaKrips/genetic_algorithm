import pandas as pd
import re
import os

files = [
    "Raspisanie_Osen_24-25 (2).xlsx",
    "2ИС+2ИК+2ИБ.xlsx",
    "Расписание Весна 25-26 3ИС+3ИК+3ИБ.xlsx",
    "4ТФ+4РФ+4ИС+4ИК+4ИБ.xlsx"
]

# ---------- Регулярные выражения ----------
# Преподаватель: ОБЯЗАТЕЛЬНО инициалы — "Маклахова И.С.", "Пец А.В.", "Сироткина-Примак Л.С."
teacher_pattern = re.compile(
    r'([А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.?)'
)
# Fallback: фамилия без инициалов (редкий случай, например "Аникин")
teacher_fallback = re.compile(r'\b([А-ЯЁ][а-яё]{3,})\b')

room_pattern = re.compile(r'ауд\.?\s*(\d+[А-Яa-zA-Z]?(?:/\d+)?)')
# Даты: покрываем все варианты из файлов
date_prefix = re.compile(
    r'^(?:\\?\s*-?\s*\d{1,2}\.\d{2}(?:\.\d{2})?(?:\s*[-+]\s*\d{1,2}\.\d{2}(?:\.\d{2})?)?'
    r'(?:[,\s]+\d{1,2}\.\d{2}(?:\.\d{2})?)*\s*)'
)
type_pattern = re.compile(r'\((лек|лаб|пр|л\.р\.)')
online_pattern = re.compile(r'(mts\.?\s*link|webinar|онлайн|online|ЭИОС)', re.IGNORECASE)
subgroup_pattern = re.compile(r'подгр?\.?\s*(\d+)')
header_pattern = re.compile(r'(\d{2}\.\d{2}\.\d{2})\s*«([^»]+)»')

NON_TEACHERS = {"Вакансия", "Неизвестно", "Преподаватель", "Онлайн", "Ростелеком"}


def find_header_row(df):
    for row_idx in range(min(10, len(df))):
        row = df.iloc[row_idx]
        count = sum(1 for val in row
                    if not pd.isna(val) and re.search(r'\d{2}\.\d{2}\.\d{2}\s*«', str(val)))
        if count >= 2:
            return row_idx
    return None


def extract_headers(df, row_idx):
    headers = {}
    if row_idx is None:
        return headers
    row = df.iloc[row_idx]
    for col_idx, val in enumerate(row):
        if pd.isna(val):
            continue
        m = header_pattern.search(str(val))
        if m:
            headers[col_idx] = f"{m.group(1)} {m.group(2)}"
    return headers


def get_specialty(col_idx, headers):
    if not headers:
        return "?"
    candidates = [c for c in headers.keys() if c <= col_idx]
    if candidates:
        return headers[max(candidates)]
    return headers[min(headers.keys())]


def extract_teachers(cell_str):
    """
    Ищем преподавателей ТОЛЬКО после скобки с типом занятия или после запятой.
    Это гарантированно отсекает слова из названия предмета.
    """
    # Отрезаем начало до "(тип),"
    m = re.search(r'\((?:лек|лаб|пр|л\.р\.)\s*\)', cell_str)
    if m:
        tail = cell_str[m.end():]
    else:
        # Если нет типа — берём всё после первого запятого слова (редкий случай)
        tail = cell_str

    # Ищем всех с инициалами
    teachers = [t.strip() for t in teacher_pattern.findall(tail) if t.strip() not in NON_TEACHERS]

    # Если ничего не нашли — fallback (например, "Аникин")
    if not teachers:
        # ищем в хвосте после запятой
        parts = [p.strip() for p in tail.split(',')]
        for p in parts:
            if re.match(r'^[А-ЯЁ][а-яё]{3,}$', p) and p not in NON_TEACHERS:
                teachers.append(p)

    return teachers


def parse_cell(cell_str):
    info = {
        "subject": None, "lesson_type": None,
        "subgroup": None, "teachers": [],
        "room": None, "is_online": False,
    }

    type_m = type_pattern.search(cell_str)
    if type_m:
        info["lesson_type"] = type_m.group(1)

    if online_pattern.search(cell_str):
        info["is_online"] = True

    room_m = room_pattern.search(cell_str)
    if room_m:
        info["room"] = room_m.group(1)

    sub_m = subgroup_pattern.search(cell_str)
    if sub_m:
        info["subgroup"] = sub_m.group(1)

    info["teachers"] = extract_teachers(cell_str)

    # Название предмета
    clean_str = date_prefix.sub('', cell_str)
    subject_m = re.match(r'^(.*?)\s*\((?:лек|лаб|пр|л\.р\.)', clean_str)
    if subject_m:
        subject = subject_m.group(1).strip()
    else:
        subject = clean_str.split(',')[0].strip()
    info["subject"] = subject.strip(', ').strip()

    return info


# ---------- Основной проход ----------
all_data = []
seen = set()

for file in files:
    if not os.path.exists(file):
        print(f"⚠ Файл {file} не найден, пропускаем...")
        continue

    print(f"📂 Парсим: {file}")
    xls = pd.ExcelFile(file)

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet_name, header=None)
        header_row = find_header_row(df)
        headers = extract_headers(df, header_row)

        for index, row in df.iterrows():
            if index == header_row:
                continue
            for col_index, cell_value in enumerate(row):
                if pd.isna(cell_value):
                    continue

                cell_str = str(cell_value).strip()

                if not any(kw in cell_str for kw in
                           ["лек", "лаб", "пр", "ауд", "mts", "webinar", "онлайн"]):
                    continue

                key = (file, sheet_name, index, col_index)
                if key in seen:
                    continue
                seen.add(key)

                info = parse_cell(cell_str)
                specialty = get_specialty(col_index, headers)

                all_data.append({
                    "Файл": file,
                    "Лист": sheet_name,
                    "Строка": index,
                    "Колонка": col_index,
                    "Специальность": specialty,
                    "Предмет": info["subject"],
                    "Тип": info["lesson_type"] or "?",
                    "Подгруппа": info["subgroup"] or "-",
                    "Преподаватели": "; ".join(info["teachers"]) if info["teachers"] else "Не указан",
                    "Аудитория": info["room"] if info["room"] else ("Online" if info["is_online"] else "?"),
                    "Онлайн": "Да" if info["is_online"] else "Нет",
                })

result_df = pd.DataFrame(all_data)
result_df.to_csv("extracted_data_v3.csv", index=False, sep=";", encoding="utf-8-sig")

print(f"\n✅ Готово! {len(all_data)} записей → extracted_data_v3.csv")
print(f"   Уникальных предметов:  {result_df['Предмет'].nunique()}")
real_teachers = result_df[result_df['Преподаватели'] != 'Не указан']['Преподаватели'].str.split('; ').explode()
print(f"   Уникальных преподавателей: {real_teachers.nunique()}")
print(f"   Уникальных аудиторий:  {result_df['Аудитория'].nunique()}")
print(f"\n   Топ-5 преподавателей по числу пар:")
print(real_teachers.value_counts().head(5).to_string())