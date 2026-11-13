from collections import defaultdict
from config import (
    PENALTY_TEACHER_DAY, PENALTY_ROOM_SLOT, 
    PENALTY_STUDENT_2_DAY, PENALTY_STUDENT_3_DAY, 
    SLOTS_PER_DAY
)

def calculate_fitness(chromosome, exams_data):
    penalty = 0
    
    # Для быстрой проверки создаем словари занятости
    teacher_day_map = defaultdict(int)  # (препод, день) -> кол-во экзаменов
    room_slot_map = defaultdict(int)    # (аудитория, слот) -> кол-во экзаменов
    group_day_map = defaultdict(int)    # (группа, день) -> кол-во экзаменов

    for exam_idx, slot_id in enumerate(chromosome.genes):
        exam = exams_data[exam_idx]
        day_id = slot_id // SLOTS_PER_DAY # Вычисляем день (0..33)

        # 1. Проверка преподавателей (не более 1 в день)
        for teacher in exam['teachers']:
            teacher_day_map[(teacher, day_id)] += 1

        # 2. Проверка аудиторий (не более 1 в слот)
        # Онлайн-экзамены и "TBD" не занимают реальную аудиторию
        room = exam['room']
        if room not in ('Online', 'TBD'):
            room_slot_map[(room, slot_id)] += 1

        # 3. Проверка студентов (групп)
        for group in exam['groups']:
            group_day_map[(group, day_id)] += 1

    # Считаем штрафы по собранной статистике
    for (teacher, day), count in teacher_day_map.items():
        if count > 1:
            # Преподаватель не может быть на двух экзаменах в один день
            penalty += (count - 1) * PENALTY_TEACHER_DAY

    for (room, slot), count in room_slot_map.items():
        if count > 1:
            # В одной аудитории не могут сидеть 2 группы одновременно
            penalty += (count - 1) * PENALTY_ROOM_SLOT

    for (group, day), count in group_day_map.items():
        if count == 2:
            # 2 экзамена в день - мягкое нарушение
            penalty += PENALTY_STUDENT_2_DAY
        elif count >= 3:
            # 3 и более экзаменов - жесткое нарушение
            penalty += PENALTY_STUDENT_3_DAY

    chromosome.fitness = penalty
    return penalty