import os
from enum import Enum, auto

# Основная директория
project_dir = os.path.dirname(os.path.abspath(__file__))

# Список допустимых слов
# DCT = "0123456789!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~— " + \
        # "WwАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюяҔӨҺҮҤҕөһүҥ"        

only_alpha = "WАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯҔӨҺҮҤwабвгдеёжзийклмнопрстуфхцчшщъыьэюяҕөһүҥ "
only_numbers = "0123456789"
only_signs = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~—"
only_few_signs = ".,;:()-!?«»—"       
    
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

MODEL_NAME = "vgg_example"
SPELLCHECKER_DICT = "frequency_dict_ykt.json"