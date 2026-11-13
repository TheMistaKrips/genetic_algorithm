import random

class Chromosome:
    def __init__(self, num_exams, num_slots, genes=None):
        self.num_exams = num_exams
        self.num_slots = num_slots
        
        # Если гены не переданы, создаем случайное расписание
        if genes is None:
            # Каждый экзамен получает случайный слот от 0 до 67
            self.genes = [random.randint(0, num_slots - 1) for _ in range(num_exams)]
        else:
            self.genes = genes
            
        self.fitness = float('inf') # Изначально штраф бесконечен (мы минимизируем)

    def __repr__(self):
        return f"Chromosome(fitness={self.fitness})"