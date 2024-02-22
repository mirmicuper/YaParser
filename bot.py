import sqlite3
import telebot
import time

botTimeWeb = telebot.TeleBot('6174066723:AAFHxP9W7RMf3TckUBUewHJzAFe2M7hUvzM')

# Удаление webhook перед началом долгого опроса
botTimeWeb.delete_webhook()

from telebot import types

# Функция для мониторинга базы данных и отправки уведомлений
def check_notifications():
    # Подключение к базе данных SQLite внутри потока
    conn = sqlite3.connect('yadb.db')
    cursor = conn.cursor()

    while True:
        # Проверка уведомлений в базе данных
        cursor.execute("SELECT * FROM NOTIFICATIONS WHERE status = 'new'")
        notifications = cursor.fetchall()

        for notification in notifications:
            # Обновление статуса уведомления на "done"
            notification_id = notification[0]
            product_id = notification[1]
            cursor.execute("UPDATE NOTIFICATIONS SET status = 'done' WHERE id = ?", (notification_id,))
            conn.commit()

            # Получение информации о товаре из таблицы PRODUCTS
            cursor.execute("SELECT * FROM PRODUCTS WHERE id = ?", (product_id,))
            product_info = cursor.fetchone()

            # Отправка сообщения о новом уведомлении пользователям
            send_notification_to_users(product_info, conn)

        # Пауза на 5 минут перед следующей проверкой
        time.sleep(60)

# Функция для отправки уведомления пользователям
def send_notification_to_users(product_info, conn):
    bot = telebot.TeleBot('6174066723:AAFHxP9W7RMf3TckUBUewHJzAFe2M7hUvzM')  # Создаем новый экземпляр бота внутри функции

    # Формирование сообщения с информацией о товаре
    notification_message = f"ℹ️ Новый товар доступен!\n\n"
    notification_message += f"📦 Название товара: {product_info[1]}\n"
    notification_message += f"💰 Минимальная цена: {product_info[2]} руб.\n"
    notification_message += f"💸 Минимальная цена со скидкой: {product_info[3]} руб.\n"
    notification_message += f"🔥 Скидка: {product_info[4]}%\n"
    notification_message += f"💳 Дополнительная информация: {product_info[5]}\n"
    notification_message += f"💥 Промокод: {product_info[6]}\n"

    # Получение списка пользователей, которые взаимодействовали с ботом
    cursor = conn.cursor()  # Получаем новый курсор для текущего потока
    cursor.execute("SELECT DISTINCT user_id FROM INTERACTIONS")
    users = cursor.fetchall()

    # Отправка уведомления каждому пользователю
    for user in users:
        bot.send_message(user[0], notification_message)

# Запуск функции мониторинга базы данных в отдельном потоке
import threading
threading.Thread(target=check_notifications).start()

# Продолжение работы бота
from telebot import types

@botTimeWeb.message_handler(commands=['start'])
def startBot(message):
    # Подключение к базе данных SQLite внутри функции
    conn = sqlite3.connect('yadb.db')
    cursor = conn.cursor()

    user_id = message.from_user.id
    cursor.execute("INSERT INTO INTERACTIONS (user_id, interaction_time) VALUES (?, ?)", (user_id, time.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()

    start_message = (
        "🤖 Бип-Буп! \n\nТеперь ты будешь получать уведомления о ценах и скидках на Яндекс Маркете. "
        "\n\n⚠️ Не выключай программу на компьютере, иначе мы потеряем связь друг с другом. "
        "\n\n🔎 Первым делом я соберу изначальную информацию с ссылок, которые ты мне предоставил. "
        "\n\n🛍️ Затем я буду мониторить товары на скидки и акции. Если выйдет что-то новенькое, подходящее обговоренным условиям, я тебе обязательно сообщу. "
        "\n\nУдачи! 🚀"
    )
    botTimeWeb.send_message(message.chat.id, start_message, parse_mode='html')

botTimeWeb.infinity_polling()
