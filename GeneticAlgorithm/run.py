import json
import matplotlib.pyplot as plt
import os
import csv
from config import INPUT_JSON, OUTPUT_DIR
from ga import GeneticAlgorithm

def main():
    print(f"📂 Загрузка данных из {INPUT_JSON}...")
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        exams_data = json.load(f)
    
    print(f"✅ Загружено {len(exams_data)} экзаменов.")
    print("🧬 Запуск генетического алгоритма...\n")

    ga = GeneticAlgorithm(exams_data)
    best_chrom, history = ga.evolve()

    print("\n" + "="*40)
    print(f"🏆 ЛУЧШИЙ РЕЗУЛЬТАТ: {best_chrom.fitness} штрафных баллов")
    print("="*40)

    # 1. Сохраняем итоговое расписание
    schedule_output = []
    for i, slot_id in enumerate(best_chrom.genes):
        exam = exams_data[i]
        day = (slot_id // 2) + 1
        time_slot = "Утро" if slot_id % 2 == 0 else "Вечер"
        schedule_output.append({
            "id": exam['id'],
            "subject": exam['subject'],
            "teachers": exam['teachers'],
            "groups": exam['groups'],
            "room": exam['room'],
            "day": day,
            "time": time_slot
        })
    schedule_output.sort(key=lambda x: (x['day'], x['time']))
    
    out_file = os.path.join(OUTPUT_DIR, "best_schedule.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(schedule_output, f, ensure_ascii=False, indent=4)
    print(f"💾 Расписание сохранено в {out_file}")

    # 2. Сохраняем историю фитнеса для отчетов
    history_file = os.path.join(OUTPUT_DIR, "fitness_history.csv")
    with open(history_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Поколение", "Штрафные_баллы"])
        for gen, fit in enumerate(history, 1):
            writer.writerow([gen, fit])
    print(f"💾 История эволюции сохранена в {history_file}")

    # 3. Рисуем красивый график
    plt.style.use('seaborn-v0_8-darkgrid') # Современный стиль
    plt.figure(figsize=(12, 6))
    
    # Основная линия
    plt.plot(range(1, len(history) + 1), history, color='#005b96', linewidth=2.5, label='Лучший фитнес')
    
    # Добавляем точки
    plt.scatter(range(1, len(history) + 1), history, color='#d32f2f', s=30, zorder=5, label='Поколения')
    
    # Оформление
    plt.title("Эволюция генетического алгоритма: минимизация конфликтов", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Поколение", fontsize=12)
    plt.ylabel("Количество штрафных баллов", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    
    # Убираем верхнюю и правую рамки для легкости
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plot_file = os.path.join(OUTPUT_DIR, "fitness_plot.png")
    plt.tight_layout()
    plt.savefig(plot_file, dpi=300) # dpi=300 для печати в Word
    print(f"📈 График сохранен в {plot_file}")

if __name__ == "__main__":
    main()