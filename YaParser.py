import sys, os, re, sqlite3
import subprocess
import asyncio
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QListWidgetItem, QListWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QDialog, QTextEdit
from functools import partial
from PyQt5.QtGui import QTextCursor
from PyQt5.QtGui import QFont, QIcon, QColor
from PyQt5.QtCore import Qt, pyqtSlot, QTimer

# Получаем текущий каталог, где находится скрипт
current_dir = os.path.dirname(os.path.abspath(__file__))

# Относительный путь к файлу шрифта Inter
font_path = os.path.join(current_dir, "Inter", "static", "Inter-VariableFont_slnt,wght.ttf")


class MainWindow(QWidget):
    def __init__(self):
        # Добавление шрифта в базу данных шрифтов приложения
        # QFontDatabase.addApplicationFont(font_path)
        self.processes_started = False
        super().__init__()
        self.links_list = QListWidget()  # Define links_list here
        self.initUI()

    def initUI(self):
        self.processes = []
        # Создание объектов QFont для каждого начертания
        font_inter_bold = QFont("Inter", weight=QFont.Bold)
        font_inter_medium = QFont("Inter", weight=QFont.Medium)
        font_inter_regular = QFont("Inter")

        self.message_timer = QTimer(self)
        self.message_timer.timeout.connect(self.display_messages)
        self.message_counter = 0  # Счетчик сообщений
        self.messages = [
            "--Идет проверка ссылки",
            "--Процесс 1 запущен",
            "--Процесс 2 запущен",
            "--Процесс 3 остановлен",
            "--Процесс 4 остановлен"
        ]
        self.message_timer.start(200)  # Запуск таймера с интервалом 0.2 секунды

        # Установка размеров и заголовка окна
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('ЯПарсер')
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        # Цвет фона главного окна
        self.setStyleSheet("background-color: #0F1A2A; border-radius: 25px;")
        
        # Текст "ЯПарсер"
        title_text = "ЯПарсер"
        formatted_text = "<span style='color: #F10000;'>{}</span><span style='color: #F1F1F1;'>{}</span>".format(title_text[0], title_text[1:])
        title_label = QLabel(self)
        title_label.setText(formatted_text)
        title_label.setStyleSheet("font-size: 32px;")
        title_label.setGeometry(20, 20, 200, 50)
        title_label.setFont(font_inter_bold)
        
        # Текст "Парсер товаров маркета"
        subtitle_label = QLabel(self)
        subtitle_label.setText("Парсер товаров маркета")
        subtitle_label.setStyleSheet("color: #F1F1F1; font-size: 14px;")
        subtitle_label.setGeometry(20, 70, 200, 20)
        subtitle_label.setFont(font_inter_medium)
        
        # Кнопка свернуть
        minimize_button = QPushButton(self)
        minimize_button.setIcon(QIcon('minimize_icon.svg'))
        minimize_button.setStyleSheet("background-color: transparent;")
        minimize_button.setGeometry(700, 20, 35, 35)
        minimize_button.clicked.connect(self.minimize)
        
        # Кнопка закрыть
        close_button = QPushButton(self)
        close_button.setIcon(QIcon('close_icon.svg'))
        close_button.setStyleSheet("background-color: transparent;")
        close_button.setGeometry(740, 20, 35, 35)
        close_button.clicked.connect(self.close_application)
        
        # Поле "терминал"
        self.terminal_widget = QTextEdit(self)
        self.terminal_widget.setGeometry(25, 120, 750, 400)
        self.terminal_widget.setStyleSheet("background-color: #2E415C; border-radius: 15px; color: #F1F1F1; font-family: Courier;")
        self.terminal_widget.setReadOnly(True)
        
        # Кнопка "Старт" и "Стоп"
        self.start_stop_button = QPushButton("Старт", self)
        self.start_stop_button.setStyleSheet(
            "QPushButton { background-color: #2E415C; color: #F1F1F1; font-size: 16px; border-radius: 10px; }"
            "QPushButton:hover { background-color: #576885; }"  # Изменение цвета при наведении
            "QPushButton:pressed { background-color: #35445A; }"  # Изменение цвета при нажатии
        )
        self.start_stop_button.setGeometry(25, 540, 130, 35)
        self.start_stop_button.clicked.connect(self.toggle_start_stop)

        # Кнопка "конфигурация"
        self.config_button = QPushButton("Конфигурация", self)
        self.config_button.setStyleSheet(
            "QPushButton { background-color: #2E415C; color: #F1F1F1; font-size: 16px; border-radius: 10px; }"
            "QPushButton:hover { background-color: #576885; }"  # Изменение цвета при наведении
            "QPushButton:pressed { background-color: #35445A; }"  # Изменение цвета при нажатии
        )
        self.config_button.setGeometry(170, 540, 160, 35)
        self.config_button.setFont(font_inter_regular)
        self.config_button.clicked.connect(self.openConfigurationPage)
        
        # Label для ошибок
        error_label = QLabel(self)
        error_label.setStyleSheet("color: #F1F1F1; font-size: 16px;")
        error_label.setGeometry(340, 540, 370, 32)
        error_label.setFont(font_inter_regular)
        
        # Кнопка "?"
        self.help_button = QPushButton("?", self)
        self.help_button.setStyleSheet(
            "QPushButton { background-color: #2E415C; color: #F1F1F1; font-size: 16px; border-radius: 10px; }"
            "QPushButton:hover { background-color: #576885; }"  # Изменение цвета при наведении
            "QPushButton:pressed { background-color: #35445A; }"  # Изменение цвета при нажатии
        )
        self.help_button.setGeometry(720, 540, 35, 35)
        self.help_button.setFont(font_inter_regular)
        self.help_button.clicked.connect(self.openHelpDialog)

    def display_messages(self):
        # Отображение сообщений в поле "терминал"
        if self.message_counter < len(self.messages):
            self.terminal_widget.append(self.messages[self.message_counter])

            # Проверка, если количество строк в поле "терминал" превышает 500, удаляем первые 100 строк
            if self.terminal_widget.document().blockCount() > 500:
                cursor = self.terminal_widget.textCursor()
                cursor.movePosition(QTextCursor.Start)
                cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 100)
                cursor.removeSelectedText()

            self.message_counter += 1

    def minimize(self):
        self.showMinimized()

    def openHelpDialog(self):
        help_dialog = HelpDialog()
        help_dialog.exec_()
    
    def openConfigurationPage(self):
        self.config_page = ConfigurationPage(links_list=self.links_list)
        self.config_page.show()

    def toggle_start_stop(self):
        if not self.processes_started:
            self.start_processes()
            self.start_stop_button.setText("Стоп")
            self.messages.append("Processes started.")
            self.message_timer.start(200)  # Запуск таймера с интервалом 0.2 секунды для вывода сообщений
        else:
            self.stop_processes()
            self.start_stop_button.setText("Старт")
            self.messages.append("Processes stopped.")
            self.message_timer.stop()  # Остановка таймера после остановки процессов

        self.processes_started = not self.processes_started

    def start_processes(self):
        for command in [['python3', 'my_parser.py'], ['python3', 'bot.py']]:
            process = subprocess.Popen(command)
            self.processes.append(process)

    def stop_processes(self):
        for process in self.processes:
            process.terminate()

    def close_application(self):
        # Завершаем все процессы
        self.stop_processes()
        # Закрываем главное окно
        self.close()




class HelpDialog(QDialog):
    def __init__(self):
        super().__init__()

        font_inter_bold = QFont("Inter", weight=QFont.Bold)
        font_inter_medium = QFont("Inter", weight=QFont.Medium)
        font_inter_regular = QFont("Inter")

        self.setWindowTitle("Справка")
        self.setGeometry(300, 300, 400, 200)

        layout = QVBoxLayout()

        # Текст справки
        help_text = QLabel("Текст справки здесь")
        help_text.setStyleSheet("color: #F1F1F1; font-size: 16px;")
        help_text.setFont(font_inter_regular)
        layout.addWidget(help_text)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #0F1A2A; border-radius: 15px; color: #F1F1F1; font-size: 16px;")

class LinkWidget(QWidget):
    def __init__(self, link_text, discount_text="", list_widget=None, links_list=None):
        super().__init__()

        self.links_list = links_list  # Сохраняем ссылку на список виджетов

        font_inter_bold = QFont("Inter", weight=QFont.Bold)
        font_inter_medium = QFont("Inter", weight=QFont.Medium)
        font_inter_regular = QFont("Inter")

        self.link_text = link_text
        self.list_widget = list_widget

        self.link_label = QLabel(link_text)
        self.link_label.setMaximumWidth(550)  # Установим максимальную ширину для ссылки
        self.discount_input = QLineEdit()
        self.discount_input.setPlaceholderText("% скидки")
        if discount_text != "":
            self.discount_input = QLineEdit(str(discount_text))
        self.discount_input.setStyleSheet("font-size: 16px;")
        self.discount_input.setMaxLength(2)  # Установка максимальной длины ввода
        self.discount_input.setMaximumWidth(80)  # Установим максимальную ширину для поля ввода скидки
        self.discount_input.textChanged.connect(self.update_placeholder)
        self.delete_button = QPushButton("Удалить")
        self.delete_button.setStyleSheet(
            "QPushButton { background-color: #2E415C; color: #F1F1F1; font-size: 12px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #576885; }"  # Изменение цвета при наведении
            "QPushButton:pressed { background-color: #35445A; }"  # Изменение цвета при нажатии
        )
        self.delete_button.setMaximumWidth(60)  # Установим максимальную ширину для кнопки удаления
        self.delete_button.setStyleSheet("background-color: #2E415C; color: #F1F1F1; font-size: 12px; border-radius: 5px; width: 60px; height: 15px;")
        self.delete_button.clicked.connect(self.delete_item)

        self.link_number_label = QLabel()
        self.link_number_label.setStyleSheet("font-size: 16px;")
        self.link_number_label.setText(str(self.list_widget.count() + 1))

        layout = QHBoxLayout()
        layout.addWidget(self.link_number_label)
        layout.addWidget(self.link_label)
        layout.addWidget(self.discount_input)
        layout.addWidget(self.delete_button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Подключение обработчика для валидации скидки
        self.discount_input.textChanged.connect(self.validate_discount)

    def delete_item(self):
        index = self.list_widget.indexFromItem(self.list_widget.itemAt(self.pos()))
        if index.isValid():
            self.list_widget.takeItem(index.row())
            # После удаления элемента обновляем индексы всех виджетов в списке
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                widget = self.list_widget.itemWidget(item)
                widget.link_number_label.setText(str(i + 1))



    def update_placeholder(self, text):
        # Если текст пустой, устанавливаем placeholder
        if not text:
            self.discount_input.setPlaceholderText("% скидки")
        else:
            self.discount_input.setPlaceholderText("")

    def validate_discount(self, text):
        # Проверка на пустой ввод
        if not text:
            return
        # Проверка на соответствие формату числа от 1 до 99, исключая 0
        pattern = re.compile(r'^[1-9][0-9]?$')
        if not pattern.match(text):
            # Сбросить значение поля
            self.discount_input.clear()
    

class ConfigurationPage(QWidget):
    def __init__(self, parent=None, links_list=None):
        super().__init__(parent)
        self.links_list = QListWidget()
        self.load_links_from_database()
        self.setWindowTitle("Конфигурация")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setStyleSheet("background-color: #0F1A2A; border-radius: 25px; color: #F1F1F1; font-size: 16px;")

        font_inter_bold = QFont("Inter", weight=QFont.Bold)
        font_inter_medium = QFont("Inter", weight=QFont.Medium)
        font_inter_regular = QFont("Inter")

        layout = QVBoxLayout()

        # Текст "ЯПарсер"
        title_text = "ЯПарсер"
        formatted_text = "<span style='color: #F10000;'>{}</span><span style='color: #F1F1F1;'>{}</span>".format(title_text[0], title_text[1:])
        title_label = QLabel(formatted_text)
        title_label.setStyleSheet("font-size: 32px;")
        title_label.setFont(font_inter_bold)
        layout.addWidget(title_label)

        # Текст "Парсер товаров маркета"
        subtitle_label = QLabel("Парсер товаров маркета")
        subtitle_label.setStyleSheet("font-size: 14px;")
        subtitle_label.setFont(font_inter_medium)
        layout.addWidget(subtitle_label)

        # Кнопка свернуть
        minimize_button = QPushButton(self)
        minimize_button.setIcon(QIcon('minimize_icon.svg'))
        minimize_button.setStyleSheet("background-color: transparent;")
        minimize_button.setGeometry(700, 20, 35, 35)
        minimize_button.clicked.connect(self.minimize)
        
        # Кнопка закрыть
        close_button = QPushButton(self)
        close_button.setIcon(QIcon('close_icon.svg'))
        close_button.setStyleSheet("background-color: transparent;")
        close_button.setGeometry(740, 20, 35, 35)
        close_button.clicked.connect(self.close)
        
        # Надпись "Ссылки"
        links_label = QLabel("Ссылки")
        links_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        links_label.setAlignment(Qt.AlignCenter)  # Выравнивание по центру
        layout.addWidget(links_label)

        # Горизонтальный layout для инпута и кнопки
        input_layout = QHBoxLayout()

        # Инпут для ввода ссылок
        self.links_input = QLineEdit(self)  # Make links_input an attribute of ConfigurationPage
        self.links_input.setPlaceholderText("Вставьте одну/несколько ссылок")
        self.links_input.setStyleSheet("font-size: 16px; padding-left: 10px; background-color: #F1F1F1; color: #000000; border: 1px solid #D9D9D9; border-radius: 10px; width: 440px; height: 35px;")
        input_layout.addWidget(self.links_input)

        # Кнопка "добавить"
        add_button = QPushButton("Добавить")
        add_button.setStyleSheet(
            "QPushButton { background-color: #2E415C; color: #F1F1F1; font-size: 16px; border-radius: 10px; width: 130px; height: 35px;}"
            "QPushButton:hover { background-color: #576885; }"  # Изменение цвета при наведении
            "QPushButton:pressed { background-color: #35445A; }"  # Изменение цвета при нажатии
        )
        add_button.clicked.connect(self.add_links)
        input_layout.addWidget(add_button)

        # Добавляем горизонтальный layout в основной вертикальный layout
        layout.addLayout(input_layout)

        # self.links_list = QListWidget()
        layout.addWidget(self.links_list)
        # Список для отображения ссылок
        self.links_list_widget = QListWidget()  # Переименовываем атрибут для различения от атрибута класса
        layout.addWidget(self.links_list_widget)

        # Колесо прокрутки для списка ссылок
        self.links_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Добавим кнопку "Сохранить" внизу окна
        save_button = QPushButton("Сохранить")
        save_button.setStyleSheet(
            "QPushButton { background-color: #2E415C; color: #F1F1F1; font-size: 16px; border-radius: 10px; width: 130px; height: 35px;}"
            "QPushButton:hover { background-color: #576885; }"  # Изменение цвета при наведении
            "QPushButton:pressed { background-color: #35445A; }"  # Изменение цвета при нажатии
        )
        save_button.clicked.connect(self.save_data)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def update_indexes(self):
        for i in range(self.links_list.count()):
            item = self.links_list.item(i)
            widget = self.links_list.itemWidget(item)
            widget.link_number_label.setText(str(i + 1))

    def minimize(self):
        self.showMinimized()

    def add_links(self):
        global links_list
        links_text = self.links_input.text()
        links = links_text.split('\n')
        for link in links:
            if link.strip():
                item = QListWidgetItem()
                item_widget = LinkWidget(link, "", list_widget=self.links_list_widget)
                item.setSizeHint(item_widget.sizeHint())
                self.links_list.addItem(item)
                self.links_list.setItemWidget(item, item_widget)
        self.links_input.clear()  # Очистка инпута после добавления данных
        self.update_indexes()  # Обновление индексов после добавления элементов

    def load_links_from_database(self):
        # Устанавливаем соединение с базой данных
        conn = sqlite3.connect('yadb.db')
        c = conn.cursor()
        
        # Запрос для выборки всех ссылок из таблицы LINKS
        c.execute("SELECT link, discount FROM LINKS")
        
        # Получаем результаты запроса
        links = c.fetchall()
        print(links)
        
        # Очищаем список перед добавлением новых значений
        self.links_list.clear()
        
        # Добавляем ссылки в список
        for link_data in links:
            link_text, discount_text = link_data
            # Преобразование None в пустую строку для discount_text
            if discount_text is None:
                discount_text = ""
            item = QListWidgetItem()
            item_widget = LinkWidget(link_text, discount_text, list_widget=self.links_list)
            item.setSizeHint(item_widget.sizeHint())
            self.links_list.addItem(item)
            self.links_list.setItemWidget(item, item_widget)
        
        # Закрываем соединение с базой данных
        conn.close()

    def save_data(self):
        # Проверяем все инпуты скидок
        all_discounts_valid = True
        for i in range(self.links_list.count()):
            item = self.links_list.item(i)
            widget = self.links_list.itemWidget(item)
            if not widget.discount_input.text():
                widget.discount_input.setStyleSheet("border: 1px solid red;")
                all_discounts_valid = False
            else:
                widget.discount_input.setStyleSheet("")
        
        if all_discounts_valid:
            # Если все скидки введены, сохраняем данные в базу данных
            conn = sqlite3.connect('yadb.db')
            c = conn.cursor()
            c.execute("DELETE FROM LINKS")
            for i in range(self.links_list.count()):
                item = self.links_list.item(i)
                widget = self.links_list.itemWidget(item)
                link = widget.link_text
                discount = widget.discount_input.text()
                c.execute("INSERT INTO LINKS (link, discount) VALUES (?, ?)", (link, discount))
            conn.commit()
            conn.close()
            
            # Закрываем окно конфигурации
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

