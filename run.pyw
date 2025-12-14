import os
import fitz # библиотека для обработки PDF
import csv
from easyocr import Reader
from spellchecker import SpellChecker
from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtGui import QPixmap, QImage, QTextCursor, QTextCharFormat, QMouseEvent, QWheelEvent, QPainter
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication, QMenu, QFileDialog, QAction, QMessageBox
from PyQt5.QtWidgets import QPushButton, QListWidget, QLabel, QTextEdit, QSpinBox

from utils import *

# Класс для замены QLabel для реализации зума и перемещения
class ZoomLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.pixmap_original = QPixmap()
        self.scale = 1.0
        self.offset = QPoint(0, 0)
        self.drag_start = None

        self.setMouseTracking(True)

    def setImage(self, path):
        self.pixmap_original = QPixmap(path)
        self.scale = 1.0
        self.offset = QPoint(0, 0)
        self.update()

    def wheelEvent(self, event: QWheelEvent):
        old_scale = self.scale

        if event.angleDelta().y() > 0:
            self.scale *= 1.1
        else:
            self.scale /= 1.1

        # Ограничение масштаба
        self.scale = max(0.1, min(5, self.scale))

        # Центрируем зум относительно курсора
        mouse_pos = event.pos()
        delta = mouse_pos - self.offset
        self.offset -= (delta * (self.scale / old_scale - 1))

        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_start = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drag_start is not None:
            diff = event.pos() - self.drag_start
            self.offset += diff
            self.drag_start = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_start = None

    def paintEvent(self, event):
        painter = QPainter(self)

        if not self.pixmap_original.isNull():
            w = int(self.pixmap_original.width() * self.scale)
            h = int(self.pixmap_original.height() * self.scale)

            scaled = self.pixmap_original.scaled(
                w, h,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            painter.drawPixmap(self.offset, scaled)

# Класс для переопределения QSpinBox для обработки Enter
class IndexSpinBox(QSpinBox):
    def __init__(self, func, parent = None):
        super().__init__(parent)
        self.func = func
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # сюда можешь вызвать любую функцию
            self.func()
        else:
            super().keyPressEvent(event)
            
# class SettingsDialog(QtWidgets.QDialog):
#     settings_applied = QtCore.pyqtSignal(object)   # ← сигнал

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         uic.loadUi("setting_shell.ui", self)
#         self.ok_btn.clicked.connect(self.on_apply)
#         self.cancel_btn.clicked.connect(self.reject)
#         self.model_dict = {}
#         self.scDict_dict = {}
#         self.load_csv_to_list_for_models(os.path.join(project_dir, "models", "models_names.csv"))
#         self.load_csv_to_list_for_spcheck_dict(os.path.join(project_dir, "dict", "dict_names.csv"))

#     def load_csv_to_list_for_models(self, filename):
#         """Загружаем CSV, в лист отображаем только ключи"""
#         self.modelsList.clear()
#         self.dictList.clear()
#         self.model_dict.clear()
#         self.scDict_dict.clear()

#         with open(filename, newline='', encoding='utf-8') as csvfile:
#             reader = csv.reader(csvfile)
#             for row in reader:
#                 for item in row:
#                     if ":" in item:
#                         key, value = item.split(":", 1)
#                         key = key.strip()
#                         value = value.strip()
#                         self.model_dict[key] = value
#                         # В QListWidget отображаем только ключ
#                         lw_item = QtWidgets.QListWidgetItem(key)
#                         lw_item.setFlags(lw_item.flags() | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
#                         self.modelsList.addItem(lw_item)
    
#     def load_csv_to_list_for_spcheck_dict(self, filename):
#         """Загружаем CSV, в лист отображаем только ключи"""
#         self.dictList.clear()
#         self.scDict_dict.clear()

#         with open(filename, newline='', encoding='utf-8') as csvfile:
#             reader = csv.reader(csvfile)
#             for row in reader:
#                 for item in row:
#                     if ":" in item:
#                         key, value = item.split(":", 1)
#                         key = key.strip()
#                         value = value.strip()
#                         self.scDict_dict[key] = value
#                         # В QListWidget отображаем только ключ
#                         lw_item = QtWidgets.QListWidgetItem(key)
#                         lw_item.setFlags(lw_item.flags() | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
#                         self.dictList.addItem(lw_item)

#     def build_allowed_chars(self):
#         allowed = only_alpha

#         if self.numbersBox.isChecked():
#             allowed += only_numbers
#         if self.signBox.isChecked():
#             allowed += only_signs
#         if self.fewSignBox.isChecked():
#             allowed += only_few_signs

#         return "".join(sorted(set(allowed)))

#     def on_apply(self):
#         allowed_chars = self.build_allowed_chars()
#         selected_models = self.modelsList.selectedItems()
#         selected_scDicts = self.dictList.selectedItems()
        
#         model_value = ""
#         if selected_models:
#             key = selected_models[0].text()
#             model_value = self.model_dict.get(key, "")
            
#         scDict_value = ""
#         if selected_scDicts:
#             key = selected_scDicts[0].text()
#             scDict_value = self.scDict_dict.get(key, "")

#         # передаем оба значения в словаре
#         self.settings_applied.emit({
#             "allowed_chars": allowed_chars,
#             "model": model_value,
#             "scDict": scDict_value,
#         })
#         self.accept()


class SettingsDialog(QtWidgets.QDialog):
    settings_applied = QtCore.pyqtSignal(object)  # передаём словарь с данными

    def __init__(self, parent=None, default_model="", default_scDict="", default_allowed_chars=""):
        super().__init__(parent)
        uic.loadUi("setting_shell.ui", self)

        self.ok_btn.clicked.connect(self.on_apply)
        self.cancel_btn.clicked.connect(self.reject)

        # Словари для списков
        self.model_dict = {}
        self.scDict_dict = {}

        # Значения по умолчанию
        self.default_model = default_model
        self.default_scDict = default_scDict
        self.default_allowed_chars = default_allowed_chars

        # Загружаем данные в QListWidget
        self.load_csv_to_list_for_models(os.path.join(project_dir, "models", "models_names.csv"))
        self.load_csv_to_list_for_spcheck_dict(os.path.join(project_dir, "dict", "dict_names.csv"))

        # Подсветка текущих или дефолтных значений
        self.highlight_current_selection()

        # **Не трогаем чекбоксы, они работают как раньше**
        # self.restore_checkbox_state() убираем или оставляем пустым

    def load_csv_to_list_for_models(self, filename):
        self.modelsList.clear()
        self.model_dict.clear()
        with open(filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                for item in row:
                    if ":" in item:
                        key, value = item.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        self.model_dict[key] = value
                        lw_item = QtWidgets.QListWidgetItem(key)
                        lw_item.setFlags(lw_item.flags() | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                        self.modelsList.addItem(lw_item)

    def load_csv_to_list_for_spcheck_dict(self, filename):
        self.dictList.clear()
        self.scDict_dict.clear()
        with open(filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                for item in row:
                    if ":" in item:
                        key, value = item.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        self.scDict_dict[key] = value
                        lw_item = QtWidgets.QListWidgetItem(key)
                        lw_item.setFlags(lw_item.flags() | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                        self.dictList.addItem(lw_item)

    def highlight_current_selection(self):
        """Выделяем элементы, соответствующие текущим или дефолтным значениям"""
        # Модель
        model_to_select = self.default_model if self.default_model else ""
        for i in range(self.modelsList.count()):
            item = self.modelsList.item(i)
            if self.model_dict.get(item.text(), "") == model_to_select:
                item.setSelected(True)

        # Словарь
        scDict_to_select = self.default_scDict if self.default_scDict else ""
        for i in range(self.dictList.count()):
            item = self.dictList.item(i)
            if self.scDict_dict.get(item.text(), "") == scDict_to_select:
                item.setSelected(True)

    # **Чекбоксы оставляем как раньше**
    def build_allowed_chars(self):
        allowed = only_alpha
        if self.numbersBox.isChecked():
            allowed += only_numbers
        if self.signBox.isChecked():
            allowed += only_signs
        if self.fewSignBox.isChecked():
            allowed += only_few_signs
        return "".join(sorted(set(allowed)))

    def on_apply(self):
        allowed_chars = self.build_allowed_chars()

        selected_models = self.modelsList.selectedItems()
        model_value = ""
        if selected_models:
            key = selected_models[0].text()
            model_value = self.model_dict.get(key, "")

        selected_scDicts = self.dictList.selectedItems()
        scDict_value = ""
        if selected_scDicts:
            key = selected_scDicts[0].text()
            scDict_value = self.scDict_dict.get(key, "")

        self.settings_applied.emit({
            "allowed_chars": allowed_chars,
            "model": model_value,
            "scDict": scDict_value,
        })
        self.accept()
    

class MyWindow(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        # Выделенный файл
        # При изменении режима возвращается к значению None
        self.pre_selected_file = None
        # Выбранный файл
        self.selected_file = None
        # Путь до выбранного изображения
        self.path_to_file = None
        # Список файлов в папке data (по умолчанию)
        FILES = list(os.listdir(DirOfData.image.value))
        # Флаг для отключения/включения работы spellchecker
        self.pickoutflag = False
        # Флаг для переключения режима между Изображения/PDF
        self.read_regimeflag = TypeOfData.image
        # Флаг для работающего режима Изображения/PDF
        # Необходимо для генерации после предобработки, чтобы настройка не слетала
        self.process_regimeflag = None
        # Переменная для хранения страницы PDF в виде изображения
        self.pix_pdf = None
        
        # Начальный словарь допустимых символов
        self.dct = only_alpha + only_few_signs
        # Начальная модель для обработки
        self.model = MODEL_NAME
    
        # Подключение UI файла
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(os.path.join(project_dir, "qt_shell.ui"), self)
        
        # Явное указание объектов
        self.process_btn = self.findChild(QPushButton, 'process_btn')  # Ищем кнопку с именем 'pushButton'
        self.select_btn = self.findChild(QPushButton, 'select_btn')
        self.update_btn = self.findChild(QPushButton, 'update_btn')
        self.lower_btn = self.findChild(QPushButton, 'lower_btn')
        self.magic_btn = self.findChild(QPushButton, 'magic_btn')
        self.pickout_btn = self.findChild(QPushButton, 'pickout_btn')
        self.copy_btn = self.findChild(QPushButton, 'copy_btn')
        self.save_btn = self.findChild(QPushButton, 'save_btn')
        self.labelOCR = self.findChild(QLabel, 'labelOCR')
        self.textLabel = self.findChild(QTextEdit, 'textLabel')
        self.listFiles = self.findChild(QListWidget, 'listFiles')
        self.pdf_btn = self.findChild(QPushButton, 'pdf_btn')
        self.image_btn = self.findChild(QPushButton, 'image_btn')
        self.spin_pdf = self.findChild(QSpinBox, 'spin_pdf')
        self.preprocess_btn = self.findChild(QPushButton, 'preprocess_btn')
        
        # Добавление изображений в лист
        # self.listFiles.addItems(self.FILES)
        
        # Регистрация нажатий кнопок
        self.update_btn.clicked.connect(self.update_clicked)
        self.listFiles.itemClicked.connect(self.list_item_clicked)
        self.select_btn.clicked.connect(self.select_clicked)
        self.process_btn.clicked.connect(self.process_clicked)
        self.lower_btn.clicked.connect(self.lower_clicked)
        self.pickout_btn.clicked.connect(self.pickout_clicked)
        self.magic_btn.clicked.connect(self.magic_clicked)
        self.copy_btn.clicked.connect(self.copy_clicked)
        self.save_btn.clicked.connect(self.save_clicked)
        self.image_btn.clicked.connect(self.image_clicked)
        self.pdf_btn.clicked.connect(self.pdf_clicked)
        self.preprocess_btn.clicked.connect(self.open_settings)
        
        # Переопределение контекстного меню
        self.textLabel.contextMenuEvent = self.customContextMenuEvent
        
        # Реализация перетаскивания и зума в части
        self.zoom_label = ZoomLabel(self)
        self.zoom_label.setGeometry(self.labelOCR.geometry())
        layout = self.labelOCR.parentWidget().layout()
        if layout is not None:
            layout.replaceWidget(self.labelOCR, self.zoom_label)
        self.labelOCR.hide()
        spin_pdf = IndexSpinBox(self.select_clicked, self)
        spin_pdf.setGeometry(self.spin_pdf.geometry())
        spin_pdf.setValue(self.spin_pdf.value())
        layout_2 = self.spin_pdf.parentWidget().layout()
        if layout_2 is not None:
            layout_2.replaceWidget(self.spin_pdf, spin_pdf)
        self.spin_pdf.deleteLater()
        self.spin_pdf = spin_pdf
        
    # Реализация окна настройки
    def open_settings(self):
        global MODEL_NAME
        global SPELLCHECKER_DICT
        self.settings_dialog = SettingsDialog(
            self,
            default_model=getattr(self, "current_model", MODEL_NAME),
            default_scDict=getattr(self, "current_scDict", SPELLCHECKER_DICT),
            default_allowed_chars=getattr(self, "dct", self.dct)
        )
        self.settings_dialog.settings_applied.connect(self.on_settings_applied)
        self.settings_dialog.exec_()
    def on_settings_applied(self, data):
        global MODEL_NAME
        global SPELLCHECKER_DICT 
        self.dct = data["allowed_chars"]
        MODEL_NAME = data["model"]
        SPELLCHECKER_DICT = data["scDict"]
        print(MODEL_NAME)
        print(self.dct)
        print(SPELLCHECKER_DICT)
    
    # Функция для определения события закрытия окна
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Подтверждение", "Вы уверены, что хотите выйти?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            event.accept()  # Закрываем окно
        else:
            event.ignore()  # Отменяем закрытие окна
    
    # Функция для обработки клика по списку листа
    def list_item_clicked(self, item):
        if self.read_regimeflag == TypeOfData.image:
            self.pre_selected_file = item.text()
        elif self.read_regimeflag == TypeOfData.pdf:
            self.pre_selected_file = item.text()
            self.spin_pdf.setValue(1)    
    
    # Пользовательская функция для переопределения обработки контекстного меню ПКМ    
    def customContextMenuEvent(self, event):
        cursor = self.textLabel.textCursor()
        cursor.select(cursor.WordUnderCursor)
        selected_text = cursor.selectedText()
        low_selected_text = selected_text.lower()
        
        # Создаем контекстное меню
        contextMenu = QMenu(self.textLabel)
        
        contextMenu.setStyleSheet("""
        QMenu { background: white; border: 1px solid gray; }
        QMenu::item { padding: 5px 20px; }
        QMenu::item:selected { background: #e0e0e0; }
        """)
        
        spellflag = False
        
        # Добавляем действия с надписями
        cutAction = QAction("Вырезать", self.textLabel)
        copyAction = QAction("Копировать", self.textLabel)
        pasteAction = QAction("Вставить", self.textLabel)
        
        upperAction = QAction("ВСЕ ПРОПИСНЫЕ", self.textLabel)
        capitalAction = QAction("Первая буква", self.textLabel)
        lowerAction = QAction("все строчные", self.textLabel)

        
        # Добавляем действия в контекстное меню
        if self.pickoutflag and selected_text and \
            low_selected_text in self.misspelled:
                candidates = self.spell.candidates(low_selected_text)
                if candidates:
                    spellflag = True
                    spellActions = []
                    spellwords = []
                    for word in candidates:
                        spellActions.append(QAction(f"{word}", self.textLabel))
                        contextMenu.addAction(spellActions[-1])
                        spellwords.append(word)
                    contextMenu.addSeparator()
        
        contextMenu.addAction(cutAction)
        contextMenu.addAction(copyAction)
        contextMenu.addAction(pasteAction)
        
        contextMenu.addSeparator()
        contextMenu.addAction(upperAction)
        contextMenu.addAction(capitalAction)
        contextMenu.addAction(lowerAction)
        
        # Показать контекстное меню
        action = contextMenu.exec(self.textLabel.mapToGlobal(event.pos()))
        
        # Обрабатываем выбор действия
        if action == cutAction:
            self.textLabel.cut()
        elif action == copyAction:
            self.textLabel.copy()
        elif action == pasteAction:
            self.textLabel.paste()
        elif action == upperAction:
            cursor.insertText(selected_text.upper())
        elif action == capitalAction:
            # Первая буква заглавная, остальные строчные
            cursor.insertText(selected_text.capitalize())
        elif action == lowerAction:
            cursor.insertText(selected_text.lower())
        elif spellflag:
            if action in spellActions:
                insert_spellword = spellwords[spellActions.index(action)]
                if selected_text[0].isupper():
                    if selected_text.isupper():
                        insert_spellword = insert_spellword.upper()
                    else:
                        insert_spellword = insert_spellword[0].upper() + insert_spellword[1:]
                cursor.insertText(insert_spellword)
  
    
    # Метод для токенизации выведенного текста
    @staticmethod
    def splittingText(text):
        lst = list(text)
        out_lst = []
        s = ""
        f = True
        for i, el in enumerate(lst):
            if el.isalpha() == f:
                s += el
                if i == len(lst) - 1:
                    out_lst.append(s)
                continue
            out_lst.append(s)
            s = el
            f = not f
            if i == len(lst) - 1:
                    out_lst.append(s)
        return out_lst    
    
    def image_clicked(self):
        self.read_regimeflag = TypeOfData.image
        self.pre_selected_file = None
        self.update_clicked()
        
    def pdf_clicked(self):
        self.read_regimeflag = TypeOfData.pdf
        self.pre_selected_file = None
        self.update_clicked()
    
    def update_clicked(self):
        if self.read_regimeflag == TypeOfData.image:
            self.FILES = list(os.listdir(DirOfData.image.value))
            self.listFiles.clear()
            self.listFiles.addItems(self.FILES)
        elif self.read_regimeflag == TypeOfData.pdf:
            self.FILES = list(os.listdir(DirOfData.pdf.value))
            self.listFiles.clear()
            self.listFiles.addItems(self.FILES)
    
    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        super().resizeEvent(event)
        if hasattr(self, 'pixmap') and not self.pixmap.isNull():
            self.update_image()
    
    def update_image(self):
        """
        Масштабирует self.pixmap под размер QLabel и отображает его в zoom_label.
        """
        # if self.pixmap is None or self.pixmap.isNull():
        #     return

        # Масштабируем под размер QLabel, сохраняя пропорции
        scaled_pixmap = self.pixmap.scaled(
            self.zoom_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Отображаем в QLabel
        self.zoom_label.setImage(scaled_pixmap)
            
    def select_clicked(self):
        if self.pre_selected_file == None:
            return
        if self.read_regimeflag == TypeOfData.image:
            self.pixmap = QPixmap(f"{project_dir}/data/{self.pre_selected_file}")
            self.update_image()
            self.selected_file = self.pre_selected_file
            self.path_to_file = f"data/{self.selected_file}"
            self.process_regimeflag = TypeOfData.image
        elif self.read_regimeflag == TypeOfData.pdf:
            # Загрузка PDF-файла
            doc = fitz.open(f"{project_dir}/pdf_data/{self.pre_selected_file}")
            page_count = doc.page_count
            self.spin_pdf.setRange(1, page_count)
            # self.spin_pdf.setValue(1)
            current_spin = self.spin_pdf.value()
            # Отображение первой страницы PDF
            page = doc.load_page(current_spin - 1)  # Загрузка первой страницы
            zoom = 4.0
            matrix = fitz.Matrix(zoom, zoom)
            self.pix_pdf = page.get_pixmap(matrix=matrix)  # Преобразование страницы в изображение

            # Преобразование pixmap в QImage и последующее отображение в QLabel
            img = QImage(self.pix_pdf.samples, self.pix_pdf.width, 
                         self.pix_pdf.height, self.pix_pdf.stride, 
                         QImage.Format.Format_RGB888)
            self.pixmap = QPixmap.fromImage(img)
            self.update_image()
            self.selected_file = self.pre_selected_file
            self.process_regimeflag = TypeOfData.pdf
            # Закрытие документа
            doc.close()
            
    # Кнопка обработка
    # def preprocess_clicked(self):
    #     if self.selected_file == None:
    #         return
    #     if self.read_regimeflag == TypeOfData.image:
    #         filtered_image = cv2.imread(f"{project_dir}/data/{self.selected_file}")
    #         filtered_image = cv2.cvtColor(filtered_image, cv2.COLOR_BGR2GRAY)
    #         filtered_image = cv2.resize(filtered_image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    #         self.path_to_file = f"temp/temp_image_enhanced.png"
    #         cv2.imwrite(f'{project_dir}/{self.path_to_file}', filtered_image)
    #         self.pixmap = QPixmap(f"{project_dir}/{self.path_to_file}")
    #         self.update_image()
    #         self.process_regimeflag = TypeOfData.image

    def process_clicked(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Пожалуйста, подождите")
        layout = QtWidgets.QVBoxLayout(dialog)
        label = QtWidgets.QLabel("Идёт обработка, пожалуйста, не закрывайте окно...", dialog)
        layout.addWidget(label)
        dialog.setModal(True)
        dialog.show()
        
        QtWidgets.QApplication.processEvents()
        
        if self.model != MODEL_NAME or 'reader' not in self.__dict__:
            # import_Reader_from_easyocr()
            self.model = MODEL_NAME
            self.reader = Reader(['ru'], 
                                    recog_network=f"{MODEL_NAME}",
                                    user_network_directory=f"{project_dir}/models/user_network",
                                    model_storage_directory=f'{project_dir}/models/model')

        if self.process_regimeflag == TypeOfData.image:    
            result = " ".join(self.reader.readtext(f"{project_dir}/{self.path_to_file}",
                                    allowlist=self.dct, detail=0, paragraph=True))
        elif self.process_regimeflag == TypeOfData.pdf:
            self.pix_pdf.save(temp_file, "JPEG")
            result = " ".join(self.reader.readtext(temp_file, allowlist=self.dct, detail=0, paragraph=True))
        
        self.magic_clicked()
        
        dialog.close()
        
        self.textLabel.append(result)
        
    
    def lower_clicked(self):
        menu = QtWidgets.QMenu(self)

        # Добавляем действия (варианты)
        action1 = menu.addAction("Понизить буквы")
        action2 = menu.addAction("Понизить все буквы, кроме первых")

        # Обрабатываем выбор
        action1.triggered.connect(lambda: self.lower_text(1))
        action2.triggered.connect(lambda: self.lower_text(2))

        # Показываем меню прямо под кнопкой
        menu.exec_(self.lower_btn.mapToGlobal(self.lower_btn.rect().bottomLeft()))
        
    def lower_text(self, regime):
        current_text = self.textLabel.toPlainText()
        if regime == 2:
            split_text = self.splittingText(current_text)
            self.textLabel.setPlainText("".join(map(lambda x: x[0] + x[1:].lower(), split_text)))
        else:
            self.textLabel.setPlainText(current_text.lower())
        
        cursor = self.textLabel.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(QTextCharFormat())  # Сброс всех стилей
        
        self.textLabel.setTextCursor(cursor)
        
        self.pickoutflag = False
    
    # Кнопка "Выделить некорректные слова"
    def pickout_clicked(self):
        self.pickoutflag = True
        current_text = self.textLabel.toPlainText()
        lst_text = self.splittingText(current_text)
        lst_text_lower = list(map(lambda x: x.lower(), lst_text))
        lst_text_for_spell = list(filter(lambda x: x.isalpha(), lst_text_lower))
        self.spell = SpellChecker(distance=1, local_dictionary=f'{project_dir}/dict/{SPELLCHECKER_DICT}')
        self.misspelled = self.spell.unknown(lst_text_for_spell)
        for eli in self.misspelled:
            for j, elj in enumerate(lst_text_lower):
                if eli == elj:
                    if self.spell.candidates(eli):
                        lst_text[j] = \
  f"<span style=\"color: darkorange;\">{lst_text[j]}</span>"
  # f"<span style=\"background-color: moccasin;\">{lst_text[j]}</span>"
                    else:
                        lst_text[j] = \
f"<span style=\"color: red;\">{lst_text[j]}</span>"
# f"<span style=\"background-color: indianred;\">{lst_text[j]}</span>"
        joined_text = "".join(lst_text).replace("\n", "<br/>")
        self.textLabel.setHtml(joined_text)
    
    # Кнопка "Очистить"
    def magic_clicked(self):
        self.textLabel.setPlainText(self.textLabel.toPlainText())
        cursor = self.textLabel.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(QTextCharFormat())  # Сброс всех стилей

        self.textLabel.setTextCursor(cursor)
        self.pickoutflag = False
        
    def copy_clicked(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.textLabel.toPlainText())
                
    def save_clicked(self):
        # Открываем диалог сохранения файла
        file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Все файлы (*);;Текстовые файлы (*.txt)")
        if file_name:
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(self.textLabel.toPlainText())


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    # set_light_theme(app)
    window = MyWindow()
    window.setWindowTitle('Sakha_text_OCR')
    window.show()
    sys.exit(app.exec())