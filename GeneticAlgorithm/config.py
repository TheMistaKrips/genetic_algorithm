import os

# --- ПУТИ ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_JSON = os.path.join(BASE_DIR, 'processed', 'exam_list_clean.json')
OUTPUT_DIR = os.path.join(BASE_DIR, 'GeneticAlgorithm', 'output')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- ВРЕМЕННЫЕ СЛОТЫ ---
# Допустим, сессия: 12-30 декабря (19 дней) и 1-15 июня (15 дней) = 34 дня.
# По 2 экзамена в день (утро/вечер) = 68 слотов.
DAYS_COUNT = 34
SLOTS_PER_DAY = 2
TOTAL_SLOTS = DAYS_COUNT * SLOTS_PER_DAY

# --- ВЕСА ШТРАФОВ (Фитнес-функция) ---
# Чем выше число, тем страшнее нарушение
PENALTY_TEACHER_DAY = 200     # Преподаватель ведет 2+ экзамена в один день
PENALTY_ROOM_SLOT = 300       # В одной аудитории 2 экзамена в одно и то же время (утро/вечер)
PENALTY_STUDENT_2_DAY = 10    # У студента 2 экзамена в день (мягкое нарушение, разрешено)
PENALTY_STUDENT_3_DAY = 100   # У студента 3+ экзамена в день (жесткое нарушение)

# --- ПАРАМЕТРЫ ГЕНЕТИЧЕСКОГО АЛГОРИТМА ---
POPULATION_SIZE = 100         # Сколько расписаний в одном поколении
GENERATIONS = 150             # Сколько поколений будем эволюционировать
MUTATION_RATE = 0.15          # Вероятность мутации (15% генов)
TOURNAMENT_SIZE = 3           # Размер турнира при селекции
ELITISM_COUNT = 2             # Сколько лучших особей переходят в новое поколение без изменений