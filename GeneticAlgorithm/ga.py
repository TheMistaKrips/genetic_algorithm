import random
from chromosome import Chromosome
from fitness import calculate_fitness
from operators import tournament_selection, crossover, mutate
from config import POPULATION_SIZE, GENERATIONS, MUTATION_RATE, TOURNAMENT_SIZE, ELITISM_COUNT, TOTAL_SLOTS

class GeneticAlgorithm:
    def __init__(self, exams_data):
        self.exams_data = exams_data
        self.num_exams = len(exams_data)
        self.population = []
        self.best_chromosome = None
        self.history = [] # Для графика

    def init_population(self):
        """Создаем стартовую популяцию случайных расписаний"""
        self.population = [
            Chromosome(self.num_exams, TOTAL_SLOTS) 
            for _ in range(POPULATION_SIZE)
        ]
        for ind in self.population:
            calculate_fitness(ind, self.exams_data)

    def evolve(self):
        self.init_population()
        
        for gen in range(GENERATIONS):
            # Сортируем по возрастанию фитнеса (от лучшего к худшему)
            self.population.sort(key=lambda x: x.fitness)
            
            # Сохраняем лучшего
            if self.best_chromosome is None or self.population[0].fitness < self.best_chromosome.fitness:
                self.best_chromosome = self.population[0]
            
            self.history.append(self.best_chromosome.fitness)
            print(f"Поколение {gen + 1}/{GENERATIONS} | Лучший фитнес: {self.best_chromosome.fitness}")

            # Если достигли идеала (0 штрафов), нет смысла продолжать
            if self.best_chromosome.fitness == 0:
                print("🎉 Идеальное расписание найдено!")
                break

            new_population = []
            
            # Элитизм: лучшие переходят без изменений
            new_population.extend(self.population[:ELITISM_COUNT])

            # Заполняем остальную популяцию потомками
            while len(new_population) < POPULATION_SIZE:
                # Выбираем родителей
                p1 = tournament_selection(self.population, TOURNAMENT_SIZE)
                p2 = tournament_selection(self.population, TOURNAMENT_SIZE)
                
                # Скрещиваем
                child1_genes, child2_genes = crossover(p1, p2)
                
                # Мутируем
                child1_genes = mutate(child1_genes, TOTAL_SLOTS, MUTATION_RATE)
                child2_genes = mutate(child2_genes, TOTAL_SLOTS, MUTATION_RATE)
                
                # Создаем новых особей и считаем фитнес
                c1 = Chromosome(self.num_exams, TOTAL_SLOTS, child1_genes)
                c2 = Chromosome(self.num_exams, TOTAL_SLOTS, child2_genes)
                calculate_fitness(c1, self.exams_data)
                calculate_fitness(c2, self.exams_data)
                
                new_population.append(c1)
                if len(new_population) < POPULATION_SIZE:
                    new_population.append(c2)
                    
            self.population = new_population
        
        return self.best_chromosome, self.history