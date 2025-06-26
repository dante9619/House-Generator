import bpy
import math
import random

from . import object_helpers as helpers
from . import asset_loader

floor_heights = {
    ("test", "low"): 2.7, ("test", "medium"): 2.7, ("test", "high"): 2.7,
    ("japanese", "low"): 2.7, ("japanese", "medium"): 2.7, ("japanese", "high"): 2.7,
    ("stal", "low"): 3.2, ("stal", "medium"): 3.2, ("stal", "high"): 3.2,
    ("khr", "low"): 3, ("khr", "medium"): 3, ("khr", "high"): 3,
}

def generate_japanese_building(style, details, floors, seed):
    foundation = asset_loader.append_random_base(style, details)

    if not foundation:
        print("Фундамент не загружен")
        return

    floor_height = floor_heights.get((style, details), 2.7)
    scale_factor = 1.0

    for floor in range(floors):
        new_base = foundation.copy()
        new_base.data = foundation.data.copy()
        bpy.context.collection.objects.link(new_base)
        new_base.location.z = floor * floor_height
        new_base.scale *= scale_factor

        base_name_parts = foundation.name.split('_')
        if len(base_name_parts) >= 3:
            base_id = base_name_parts[-1]

        # применить трансформации
        bpy.context.view_layer.objects.active = new_base
        bpy.ops.object.transform_apply(scale=True)

        # получить сегменты
        segments = helpers.get_top_edges(new_base)

        for start, end in segments:
            direction = (end - start).normalized()
            length = (end - start).length
            walls, scale_factor = helpers.find_wall_combination(length)
            if walls:
                place_wall_segment(start, direction, walls, z=floor*floor_height+0.2, style=style, details=details, seed=seed, floors=floors, scale_factor=scale_factor)
        
        scale_factor *= 0.9

    # добавить крышу
    roof = asset_loader.append_random_roof(style, details, base_id)
    if roof:
        roof.location.z = floors * floor_height + 0.2

def generate_khrushchev_building(style, details, floors, seed):
    foundation = asset_loader.append_random_base(style, details)

    if not foundation:
        print("Фундамент не загружен")
        return

    floor_height = floor_heights.get((style, details), 2.7)

    # Словарь для хранения типов стен для каждого сегмента
    segment_wall_types = {}
    second_floor_patterns = {}

    for floor in range(floors):
        new_base = foundation.copy()
        new_base.data = foundation.data.copy()
        bpy.context.collection.objects.link(new_base)
        new_base.location.z = floor * floor_height

        base_name_parts = foundation.name.split('_')
        if len(base_name_parts) >= 3:
            base_id = base_name_parts[-1]

        bpy.context.view_layer.objects.active = new_base
        bpy.ops.object.transform_apply(scale=True)

        segments = helpers.get_top_edges(new_base)

        for i, (start, end) in enumerate(segments):
            direction = (end - start).normalized()
            length = (end - start).length
            walls, _ = helpers.find_wall_combination(length)
            
            if walls:
                # Для первого этажа определяем типы стен
                if floor == 0:
                    wall_types = []
                    for wall_len in walls:
                        keyword = f"wall{int(wall_len * 5)}"
                        rnd = random.random()
                        
                        if rnd > 0.80:  # Дверь на первом этаже
                            wall_types.append((keyword, "door"))
                        elif rnd > 0.40:  # Окно на первом этаже
                            wall_types.append((keyword, "window"))
                        else:  # Просто стена
                            wall_types.append((keyword, "plain"))
                    
                    segment_wall_types[i] = wall_types
                
                # Для второго этажа формируем паттерны
                elif floor == 1:
                    wall_patterns = []
                    for idx, (keyword, wall_type) in enumerate(segment_wall_types.get(i, [])):
                        if wall_type == "door":
                            # Дверь → окно
                            wall_patterns.append((keyword, "window"))
                        else:
                            # Окно/стена → либо повтор, либо балкон (25%)
                            if random.random() < 0.25:
                                wall_patterns.append((keyword, "balcony"))
                            else:
                                wall_patterns.append((keyword, wall_type))
                    
                    second_floor_patterns[i] = wall_patterns
                
                # Используем сохраненные типы стен
                if floor == 0:
                    wall_types = segment_wall_types.get(i, [])
                else:
                    wall_types = second_floor_patterns.get(i, [])
                
                place_soviet_wall_segment(
                    start, 
                    direction, 
                    walls, 
                    z=floor*floor_height+0.2, 
                    style=style, 
                    details=details, 
                    seed=seed, 
                    floors=floors, 
                    scale_factor=1,
                    wall_types=wall_types,
                    floor_num=floor
                )

    # Добавить крышу
    roof = asset_loader.append_random_roof(style[:3], details, base_id)
    if roof:
        roof.location.z = floors * floor_height + 0.2

def generate_stalin_building(style, details, floors, seed):
    print("generate_stalin_building")

style_generators = {
    "test": generate_japanese_building,
    "japanese": generate_japanese_building,
    "khrushchev": generate_khrushchev_building,
    "stal": generate_stalin_building,
}

def generate_building(style="japanese", details="low", floors=1, seed=101):
    print(f"\n---> Генерация здания. Стиль: {style}, Детализация: {details}, Этажей: {floors}, Сид: {seed}\n")
    random.seed(seed)
    asset_loader.clean_unused_data()

    generator_func = style_generators.get(style.lower())
    if not generator_func:
        print(f"-XXX Нет генератора для стиля: {style}")
        return

    generator_func(style, details, floors, seed)
    asset_loader.clean_unused_data()

def place_soviet_wall_segment(start, direction, walls, z=0.2, style="khrushchev", details="low", 
                                 seed=101, floors=1, scale_factor=1, wall_types=None, floor_num=0):
    cursor = start.copy()
    floor_height = floor_heights.get((style, details), 2.7)
    
    for idx, wall_len in enumerate(walls):
        scaled_len = wall_len * scale_factor
        wall_type = wall_types[idx] if (wall_types and idx < len(wall_types)) else (f"wall{int(wall_len * 5)}", "plain")
        
        keyword, type = wall_type
        blend_file = None
        obj_name = None
        
        # Логика выбора стены
        if floor_num == 0:
            # Первый этаж - используем сохраненный тип
            if type == "door":
                blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_door")
            elif type == "window":
                blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_window")
            else:
                blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_{style}")
        else:
            # Для верхних этажей используем паттерн второго этажа
            if type == "balcony":
                # Пробуем загрузить балкон
                blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_balcony")
                if not blend_file:
                    # Если балкона нет - ставим окно
                    blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_window")
            elif type == "window":
                blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_window")
            else:
                blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_{style}")

        # Фолбэк если не нашли специфичный тип
        if not blend_file:
            blend_file, obj_name = asset_loader.get_random_asset(style, details, keyword)

        if not blend_file:
            print(f"XXX- Не найдена стена с длиной {wall_len}")
            continue

        wall_obj = asset_loader.append_object_from_blend(style, details, blend_file, obj_name)
        if not wall_obj:
            print("XXX- Не удалось импортировать стену")
            continue

        # Позиционирование стены
        angle = math.atan2(direction.y, direction.x)
        wall_obj.location = (cursor.x, cursor.y, z)
        wall_obj.rotation_euler[2] = angle

        wall_obj.scale.x *= scale_factor  
        wall_obj.scale.y *= 1.0          
        wall_obj.scale.z *= 1.0

        cursor += direction.normalized() * scaled_len

def place_wall_segment(start, direction, walls, z=0.2, style="japanese", details="low", seed=101, floors=1, scale_factor=1):
    """Размещает серию стен вдоль заданного направления"""
    cursor = start.copy()
    floor_height = floor_heights.get((style, details), 2.7)
    flag_engawa = False
    for wall_len in walls:
        scaled_len = wall_len * scale_factor
        keyword = f"wall{int(wall_len * 5)}"
        blend_file = None
        engawa_obj = None
        try:
            # Логика генерации дверей, окон, стен в целом
            # TODO: настенные декорации
            if z <=0.21:
                rnd = random.random()
                if rnd > 0.80:
                    try:
                        blend_file, obj_name = asset_loader.get_random_asset(style, details, f"engawa{int(round(wall_len * 5))}")
                        engawa_obj = asset_loader.append_object_from_blend(style, details, blend_file, obj_name)
                        flag_engawa = True
                    except:
                        print(f"--- Пропущен engawa для {keyword}")
                    blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_door")

                elif rnd > 0.40:
                    blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_window")
                    if not blend_file:
                        blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_{style}")
                    engawa_obj, flag_engawa = plase_engawa(style, details, wall_len, flag_engawa)
                else:
                    blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_{style}")    
                    engawa_obj, flag_engawa = plase_engawa(style, details, wall_len, flag_engawa)

            # TODO: параметр частоты генерации окон?
            else:
                flag_engawa = False
                rnd1 = random.random()
                if rnd1 > 0.5:
                    blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_window")
                    if not blend_file:
                        blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_{style}")
                else:
                    blend_file, obj_name = asset_loader.get_random_asset(style, details, f"{keyword}_{style}")
        except Exception:
            print(f"Произошла ошибка при поиске стен")


        if not blend_file:
            blend_file, obj_name = asset_loader.get_random_asset(style, details, keyword)

        if not blend_file:
            print(f"XXX- Не найдена стена с длиной {wall_len}")
            continue

        wall_obj = asset_loader.append_object_from_blend(style, details, blend_file, obj_name)
        if not wall_obj:
            print("XXX- Не удалось импортировать стену")
            continue

        # Межэтажный элемент
        inter_obj = None 
        if floors >=2:
            try:
                blend_file, obj_name = asset_loader.get_random_asset(style, details, f"interfloor{int(round(wall_len * 5))}")
                inter_obj = asset_loader.append_object_from_blend(style, details, blend_file, obj_name)
            except:
                print(f"--- Пропущен interfloor для {keyword}")

        # Позиция и поворот
        angle = math.atan2(direction.y, direction.x)
        wall_obj.location = (cursor.x, cursor.y, z)
        wall_obj.rotation_euler[2] = angle

        wall_obj.scale.x *= scale_factor  
        wall_obj.scale.y *= 1.0          
        wall_obj.scale.z *= 1.0

        if inter_obj:
            inter_obj.location = (cursor.x, cursor.y, z)
            inter_obj.rotation_euler[2] = angle

            inter_obj.scale.x *= scale_factor  
            inter_obj.scale.y *= 1.0          
            inter_obj.scale.z *= 1.0

        if engawa_obj:
            engawa_obj.location = (cursor.x, cursor.y, z-0.2)
            engawa_obj.rotation_euler[2] = angle

            engawa_obj.scale.x *= scale_factor  
            engawa_obj.scale.y *= 1.0          
            engawa_obj.scale.z *= 1.0

        cursor += direction.normalized() * scaled_len

def plase_engawa(style, details, wall_len, flag_engawa):
    eng_rand = random.random()
    if flag_engawa == True:
        if eng_rand < 0.8:
            blend_file, obj_name = asset_loader.get_random_asset(style, details, f"engawa{int(round(wall_len * 5))}")
            engawa_obj = asset_loader.append_object_from_blend(style, details, blend_file, obj_name)
            if eng_rand < 0.2:
                flag_engawa = False
            return engawa_obj, flag_engawa
    elif not flag_engawa and eng_rand < 0.2:
        flag_engawa = True
        blend_file, obj_name = asset_loader.get_random_asset(style, details, f"engawa{int(round(wall_len * 5))}")
        engawa_obj = asset_loader.append_object_from_blend(style, details, blend_file, obj_name)
        return engawa_obj, flag_engawa

class OBJECT_OT_BuildHouse(bpy.types.Operator):
    bl_idname = "object.build_house"
    bl_label = "Build House"
    bl_description = "Generate a building using a seed"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        style = context.scene.house_style.lower()
        details = context.scene.house_details.lower()
        seed = context.scene.house_seed
        floors = context.scene.house_floors

        generate_building(style=style, details=details, seed=seed, floors=floors)
        return {'FINISHED'}

classes = (OBJECT_OT_BuildHouse,)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)