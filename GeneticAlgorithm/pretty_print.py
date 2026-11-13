import json
import pandas as pd
import os
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from config import OUTPUT_DIR

def style_base_excel(worksheet):
    """Базовое оформление: шрифты, границы, ширина колонок"""
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="005b96", end_color="005b96", fill_type="solid")
    center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    thin_border = Border(
        left=Side(style='thin', color='D3D3D3'), right=Side(style='thin', color='D3D3D3'),
        top=Side(style='thin', color='D3D3D3'), bottom=Side(style='thin', color='D3D3D3')
    )

    for col_num, value in enumerate(worksheet[1], 1):
        cell = worksheet.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
        cell.border = thin_border

    for column_cells in worksheet.columns:
        length = max(len(str(cell.value)) for cell in column_cells)
        col_letter = get_column_letter(column_cells[0].column)
        worksheet.column_dimensions[col_letter].width = min(length + 4, 50)

def style_by_teacher(worksheet):
    """Особое оформление для листа с преподавателями (цветовые блоки)"""
    thin_border = Border(
        left=Side(style='thin', color='D3D3D3'), right=Side(style='thin', color='D3D3D3'),
        top=Side(style='thin', color='D3D3D3'), bottom=Side(style='thin', color='D3D3D3')
    )
    thick_border = Border(top=Side(style='medium', color='005b96')) # Жирная линия для разделения препов
    
    current_teacher = None
    color_toggle = True
    
    for row in range(2, worksheet.max_row + 1):
        # 7-я колонка (G) - это "Преподаватели"
        teacher_cell = worksheet.cell(row=row, column=7)
        
        # Если начался новый преподаватель - меняем цвет и ставим жирную линию сверху
        if teacher_cell.value != current_teacher:
            current_teacher = teacher_cell.value
            color_toggle = not color_toggle
        
        # Выбираем цвет фона (светло-голубой или белый)
        bg_color = "E6F2FF" if color_toggle else "FFFFFF"
        
        for col in range(1, worksheet.max_column + 1):
            cell = worksheet.cell(row=row, column=col)
            cell.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            
            # Если это первая строка нового преподавателя, рисуем жирную линию сверху
            if teacher_cell.value != worksheet.cell(row=row-1, column=7).value and row > 2:
                cell.border = Border(left=Side(style='thin', color='D3D3D3'), 
                                     right=Side(style='thin', color='D3D3D3'), 
                                     bottom=Side(style='thin', color='D3D3D3'), 
                                     top=Side(style='medium', color='005b96'))
            else:
                cell.border = thin_border

def create_pretty_excel():
    input_file = os.path.join(OUTPUT_DIR, "best_schedule.json")
    output_excel = os.path.join(OUTPUT_DIR, "schedule_pretty.xlsx")

    with open(input_file, 'r', encoding='utf-8') as f:
        schedule = json.load(f)

    table_data = []
    for item in schedule:
        day = item['day']
        date_str = f"Дек, {day + 11}" if day <= 19 else f"Июнь, {day - 19}"
        
        courses = set()
        for g in item['groups']:
            try:
                courses.add(int(g.split('-')[0]))
            except:
                pass
        course_str = ", ".join([str(c) for c in sorted(courses)]) + " курс"

        table_data.append({
            "День": day,
            "Дата": date_str,
            "Время": item['time'],
            "Курс": course_str,
            "Предмет": item['subject'],
            "Группы": ", ".join(item['groups']),
            "Преподаватели": ", ".join(item['teachers']),
            "Аудитория": item['room']
        })

    df_all = pd.DataFrame(table_data)
    df_all['Время_сорт'] = df_all['Время'].map({'Утро': 1, 'Вечер': 2})
    
    # Общая сортировка для обычных вкладок
    df_sorted = df_all.sort_values(by=['День', 'Время_сорт']).drop(columns=['Время_сорт'])

    print("📊 Генерируем красивый Excel с вкладками...")
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        
        # 1. Сводное расписание (по дням)
        df_sorted.to_excel(writer, sheet_name="Сводное расписание", index=False)
        style_base_excel(writer.sheets["Сводное расписание"])

        # 2. Вкладки по курсам
        for course in [1, 2, 3, 4]:
            df_course = df_sorted[df_sorted['Курс'].str.contains(str(course))]
            if not df_course.empty:
                sheet_name = f"{course} курс"
                df_course.to_excel(writer, sheet_name=sheet_name, index=False)
                style_base_excel(writer.sheets[sheet_name])

        # 3. Вкладка по преподавателям (СПЕЦИАЛЬНАЯ)
        # Сортируем строго по имени преподавателя, затем по дню и времени
        df_teachers = df_all.sort_values(by=['Преподаватели', 'День', 'Время_сорт']).drop(columns=['Время_сорт'])
        
        # Меняем порядок колонок, чтобы Преподаватель был в центре внимания (например, на 2-е место)
        cols = ["Преподаватели", "День", "Дата", "Время", "Предмет", "Курс", "Группы", "Аудитория"]
        df_teachers = df_teachers[cols]
        
        df_teachers.to_excel(writer, sheet_name="По преподавателям", index=False)
        
        ws_teachers = writer.sheets["По преподавателям"]
        style_base_excel(ws_teachers)
        style_by_teacher(ws_teachers) # Применяем наше спец-оформление

    print(f"✅ Шикарная таблица сохранена в {output_excel}")
    print("Открывай и кайфуй! Вкладка 'По преподавателям' теперь с цветовыми блоками.")

if __name__ == "__main__":
    create_pretty_excel()