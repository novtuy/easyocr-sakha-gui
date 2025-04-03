import os
from enum import Enum, auto

# Основная директория
project_dir = os.path.dirname(os.path.abspath(__file__))

# Список допустимых слов
DCT = "0123456789!\"#$%&'()*+,-./:;<=>?@[\\]^_`" + \
        "{|}~ €«»”“¤АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюяҔӨҺҮҤҕөһүҥ"        

# Путь до временного файла изображения
temp_file = os.path.join(project_dir, 'temp', 'temp_image.png')  

# Перечисление типа данных
class TypeOfData(Enum):
    pdf = auto()
    image = auto()
    
# Перечисление директорий типов данных
class DirOfData(Enum):
    pdf = os.path.join(project_dir, 'pdf_data')
    image = os.path.join(project_dir, 'data')

