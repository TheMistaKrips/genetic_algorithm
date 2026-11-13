import random

def tournament_selection(population, k):
    """Выбираем k случайных особей и возвращаем самую лучшую (с мин. штрафом)"""
    selected = random.sample(population, k)
    selected.sort(key=lambda x: x.fitness)
    return selected[0]

def crossover(parent1, parent2):
    """Двухточечный кроссовер: берем кусок от папы, кусок от мамы."""
    length = len(parent1.genes)
    if length < 2:
        return parent1.genes[:], parent2.genes[:]
    
    # Выбираем две точки разреза
    point1 = random.randint(1, length - 2)
    point2 = random.randint(point1 + 1, length - 1)
    
    child1_genes = parent1.genes[:point1] + parent2.genes[point1:point2] + parent1.genes[point2:]
    child2_genes = parent2.genes[:point1] + parent1.genes[point1:point2] + parent2.genes[point2:]
    
    return child1_genes, child2_genes

def mutate(genes, num_slots, mutation_rate):
    """Мутация: с вероятностью mutation_rate меняем слот на случайный"""
    new_genes = genes[:]
    for i in range(len(new_genes)):
        if random.random() < mutation_rate:
            new_genes[i] = random.randint(0, num_slots - 1)
    return new_genes