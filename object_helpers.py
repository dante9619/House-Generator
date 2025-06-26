import bpy
import math
from mathutils import Vector

TOLERANCE_ANGLE = 0.01  # Допускаемая погрешность при проверке 180°
WALL_LENGTHS = [2.0, 2.4, 3.0]


def get_top_edges(obj):
    """Получает верхние (горизонтальные) грани фундамета"""
    top_edges = []
    mesh = obj.data
    obj_matrix = obj.matrix_world

    max_z = -float('inf')
    for vertex in mesh.vertices:
        world_co = obj_matrix @ vertex.co
        if world_co.z > max_z:
            max_z = world_co.z

    for edge in mesh.edges:
        v1 = obj_matrix @ mesh.vertices[edge.vertices[0]].co
        v2 = obj_matrix @ mesh.vertices[edge.vertices[1]].co

        # Если обе вершины находятся почти на одной высоте — считаем ребро горизонтальным
        if (abs(v1.z - max_z) < 0.001 and abs(v2.z - max_z) < 0.001 and abs(v1.z - v2.z) < 0.001):
            top_edges.append((v1.xy, v2.xy))

    return top_edges



def find_best_combination(A, length):
    """Находит лучшее число из массива длин A и множитель (количество стен) n, чтобы n * A[i] было близко к length (заполняемому ребру)."""
    best_number = None
    best_multiplier = 0
    min_difference = float('inf')

    for number in A:
        # Определяем наилучший множитель n
        multiplier = round(length / number)  # Округляем до ближайшего целого

        # Вычисляем разницу (абсолютное значение)
        difference = abs(length - multiplier * number)

        # Обновляем, если нашли лучшее
        if difference < min_difference:
            min_difference = difference
            best_number = number
            best_multiplier = multiplier

    # Создаем комбинацию, повторяя best_number best_multiplier раз
    best_combination = [best_number] * best_multiplier

    return best_combination, min_difference


def find_wall_combination(segment_length, wall_lengths=WALL_LENGTHS, tolerance=0.25):
    """Находит масштабируемую комбинацию из одного типа стены, максимально приближенную к нужной длине."""
    if not wall_lengths:
        return None

    combination, error = find_best_combination(wall_lengths, segment_length)
    
    if not combination:
        return None

    total_length = sum(combination)
    scale_factor = segment_length / total_length
    scale_error = abs(scale_factor - 1.0)

    if scale_error <= tolerance:
        return combination, scale_factor
    else:
        return None



def register():
    pass

def unregister():
    pass