import os, bpy, random
from pathlib import Path

# путь к общим ассетам
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# 
def get_asset_path(style: str, details: str) -> Path:
    """Возвращает корректный Path объект к папке с ассетами"""
    assets_dir = Path(__file__).parent / "assets"
    return assets_dir / style / f"{details}.blend"

def list_objects_in_blend(blend_path: Path) -> list[str]:
    """Получить список объектов внутри .blend файла"""
    with bpy.data.libraries.load(str(blend_path), link=False) as (data_from, _):
        return list(data_from.objects)

def get_random_asset(style: str, details: str, keyword: str) -> tuple[str, str] | tuple[None, None]:
    """Выбирает случайный объект по ключу из единого .blend"""
    blend_path = get_asset_path(style, details)
    if not blend_path.exists():
        print(f"Файл ассетов не найден: {blend_path}")
        return None, None

    try:
        all_objects = list_objects_in_blend(blend_path)
        matching = [name for name in all_objects if keyword.lower() in name.lower()]
        if not matching:
            print(f"Не найдено объектов с ключом '{keyword}' в {blend_path}")
            return None, None
        return blend_path.name, random.choice(matching)
    except Exception as e:
        print(f"Ошибка чтения объекта из {blend_path}: {e}")
        return None, None

def append_object_from_blend(style: str, details: str, blend_file: str, obj_name: str):
    """Импортирует объект по имени, избегая дублирования материалов и текстур"""
    try:
        blend_path = get_asset_path(style, details)
        if not blend_path.exists():
            raise FileNotFoundError(f"Файл не найден: {blend_path}")

        # Сначала получаем список материалов/изображений
        with bpy.data.libraries.load(str(blend_path), link=False) as (data_from, _):
            materials_to_load = [m for m in data_from.materials if m not in bpy.data.materials]
            images_to_load = [i for i in data_from.images if i not in bpy.data.images]

        # Загружаем объект и нужные материалы
        with bpy.data.libraries.load(str(blend_path), link=False) as (data_from, data_to):
            if obj_name not in data_from.objects:
                raise ValueError(f"Объект {obj_name} не найден в {blend_path}")
            data_to.objects = [obj_name]
            data_to.materials = materials_to_load
            data_to.images = images_to_load

        obj = data_to.objects[0]
        if not obj:
            raise RuntimeError("Импорт завершился без объекта")

        # Материалы: удаляем .001 и заменяем на существующие
        for i, mat in enumerate(obj.data.materials):
            if not mat:
                continue
            base_name = mat.name.split(".")[0]
            existing = next((m for m in bpy.data.materials if m.name.startswith(base_name)), None)
            if existing:
                obj.data.materials[i] = existing
            else:
                mat.name = base_name

        bpy.context.collection.objects.link(obj)
        return obj

    except Exception as e:
        print(f"-ХХХ Ошибка при загрузке объекта '{obj_name}' из {blend_file}: {e}")
        return None

def reuse_existing_textures(obj):
    """Заменяет текстуры объекта на уже загруженные (если есть)."""
    if not obj.data.materials:
        return

    for mat in obj.data.materials:
        if not mat or not mat.use_nodes:
            continue

        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                base_name = node.image.name.split(".")[0]
                existing_image = next(
                    (img for img in bpy.data.images 
                     if img.name == base_name or img.name.split(".")[0] == base_name),
                    None
                )
                if existing_image:
                    node.image = existing_image

def clean_unused_data():
    """Удаляет неиспользуемые материалы и текстуры."""
    for mat in bpy.data.materials:
        if mat.use_fake_user:
            mat.use_fake_user = False

    # Материалы
    for mat in bpy.data.materials:
        if mat.users == 0 and not mat.use_fake_user:
            bpy.data.materials.remove(mat)

    # Текстуры
    for img in bpy.data.images:
        if img.users == 0 and not img.use_fake_user:
            bpy.data.images.remove(img)


# пример функции добавления рандомного фундамента
def append_random_base(style, details):
    blend_file, obj_name = get_random_asset(style, details, keyword='base')

    if not blend_file:
        print(f"Фундаменты не найдены для {style}, {details}")
        return None
    return append_object_from_blend(style, details, blend_file, obj_name)

def append_random_wall15(style, details):
    blend, obj_name = get_random_asset(style, details, keyword='wall15')
    if not blend:
        print(f"Стены не найдены для {style}, {details}")
        return None
    return append_object_from_blend(style, details, blend, obj_name)

def append_random_roof(style, details, base_id):
    blend, obj_name = get_random_asset(style, details, keyword=f'roof_{style}_{details}_{base_id}')

    if not blend:
        print(f"Крыши не найдены для {style}, {details}")
        return None
    return append_object_from_blend(style, details, blend, obj_name)


def register():
    pass

def unregister():
    pass