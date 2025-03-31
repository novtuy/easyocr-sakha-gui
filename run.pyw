import os
import cv2
import fitz                                                             # библиотека для обработки PDF
from easyocr import Reader
from spellchecker import SpellChecker
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QPixmap, QImage, QTextCursor, QTextCharFormat
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMenu, QFileDialog, QAction, QMessageBox
from PyQt5.QtWidgets import QPushButton, QListWidget, QLabel, QTextEdit, QSpinBox

from utils import *

def import_Reader_from_easyocr():
    from easyocr import Reader

class MyWindow(QtWidgets.QWidget):
    MODEL_NAME = "my_example"                                     # имя выбранной модели
    
    def __init__(self, parent=None):
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
    
        # Подключение UI файла
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi("qt_shell.ui", self)
        
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
        self.preprocess_btn.clicked.connect(self.preprocess_clicked)
        
        # Переопределение контекстного меню
        self.textLabel.contextMenuEvent = self.customContextMenuEvent
        
    
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
        
        spellflag = False
        
        # Добавляем действия с русскими надписями
        cutAction = QAction("Вырезать", self.textLabel)
        copyAction = QAction("Копировать", self.textLabel)
        pasteAction = QAction("Вставить", self.textLabel)
        
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
        
        # Показать контекстное меню
        action = contextMenu.exec(self.textLabel.mapToGlobal(event.pos()))
        
        # Обрабатываем выбор действия
        if action == cutAction:
            self.textLabel.cut()
        elif action == copyAction:
            self.textLabel.copy()
        elif action == pasteAction:
            self.textLabel.paste()
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
         
    def select_clicked(self):
        if self.pre_selected_file == None:
            return
        if self.read_regimeflag == TypeOfData.image:
            self.pixmap = QPixmap(f"{project_dir}/data/{self.pre_selected_file}")
            self.labelOCR.setPixmap(self.pixmap.scaled(self.labelOCR.size(), 
                                                  aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                                                  transformMode=Qt.TransformationMode.SmoothTransformation))
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
            zoom = 6.0
            matrix = fitz.Matrix(zoom, zoom)
            self.pix_pdf = page.get_pixmap(matrix=matrix)  # Преобразование страницы в изображение

            # Преобразование pixmap в QImage и последующее отображение в QLabel
            img = QImage(self.pix_pdf.samples, self.pix_pdf.width, 
                         self.pix_pdf.height, self.pix_pdf.stride, 
                         QImage.Format.Format_RGB888)
            self.labelOCR.setPixmap(QPixmap.fromImage(img).scaled(self.labelOCR.size(), 
                                                  aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                                                  transformMode=Qt.TransformationMode.SmoothTransformation))
            self.selected_file = self.pre_selected_file
            self.process_regimeflag = TypeOfData.pdf
            # Закрытие документа
            doc.close()
            
    def preprocess_clicked(self):
        if self.selected_file == None:
            return
        if self.read_regimeflag == TypeOfData.image:
            filtered_image = cv2.imread(f"{project_dir}/data/{self.selected_file}")
            filtered_image = cv2.cvtColor(filtered_image, cv2.COLOR_BGR2GRAY)
            filtered_image = cv2.resize(filtered_image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            self.path_to_file = f"temp/temp_image_enhanced.png"
            cv2.imwrite(f'{project_dir}/{self.path_to_file}', filtered_image)
            self.pixmap = QPixmap(f"{project_dir}/{self.path_to_file}")
            self.labelOCR.setPixmap(self.pixmap.scaled(self.labelOCR.size(), 
                                                  aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                                                  transformMode=Qt.TransformationMode.SmoothTransformation))
            self.process_regimeflag = TypeOfData.image

    def process_clicked(self):
        if 'reader' not in self.__dict__:
            # import_Reader_from_easyocr()
            self.reader = Reader(['ru'], 
                                    recog_network=f"{self.MODEL_NAME}",
                                    user_network_directory=f"{project_dir}/models/user_network",
                                    model_storage_directory=f'{project_dir}/models/model')
        if self.process_regimeflag == TypeOfData.image:    
            result = " ".join(self.reader.readtext(f"{project_dir}/{self.path_to_file}",
                                    allowlist=DCT, detail=0, paragraph=True))
        elif self.process_regimeflag == TypeOfData.pdf:
            self.pix_pdf.save(temp_file, "JPEG")
            result = " ".join(self.reader.readtext(temp_file, allowlist=DCT, detail=0, paragraph=True))
            
        self.magic_clicked()
        # self.textLabel.setPlainText(result)
        self.textLabel.append(result)
    
    def lower_clicked(self):
        current_text = self.textLabel.toPlainText()
        split_text = self.splittingText(current_text)
        self.textLabel.setPlainText("".join(map(lambda x: x[0] + x[1:].lower(), split_text)))
        
        cursor = self.textLabel.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(QTextCharFormat())  # Сброс всех стилей
        
        self.textLabel.setTextCursor(cursor)
        
        self.pickoutflag = False
    
    def pickout_clicked(self):
        self.pickoutflag = True
        current_text = self.textLabel.toPlainText()
        lst_text = self.splittingText(current_text)
        lst_text_lower = list(map(lambda x: x.lower(), lst_text))
        lst_text_for_spell = list(filter(lambda x: x.isalpha(), lst_text_lower))
        self.spell = SpellChecker(distance=1, local_dictionary=f'{project_dir}/dict/frequency_dict.json')
        self.misspelled = self.spell.unknown(lst_text_for_spell)
        for eli in self.misspelled:
            for j, elj in enumerate(lst_text_lower):
                if eli == elj:
                    if self.spell.candidates(eli):
                        lst_text[j] = \
f"<span style=\"background-color: moccasin;\">{lst_text[j]}</span>"
                    else:
                        lst_text[j] = \
f"<span style=\"background-color: indianred;\">{lst_text[j]}</span>"
        joined_text = "".join(lst_text).replace("\n", "<br/>")
        self.textLabel.setHtml(joined_text)
        
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