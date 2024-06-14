import telebot
import sqlite3
from config import *
bot = telebot.TeleBot(token)
conn = sqlite3.connect('projects.db', check_same_thread=False)
c = conn.cursor()
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет! Этот бот поможет вам хранить ваши личные проекты. Для помощи пропиши /help!')
@bot.message_handler(commands=['help'])
def start_message(message):
    bot.send_message(message.chat.id, 'Все команды бота:\n/start - приветствие\n/help - помощь по всем командам\n/add - добавить новый проект\n/show - все ваши проекты\n/edit - редактирование описания проекта\n/delete - удаление проекта\n/save - сохранение ваших проектов в файл\n/find - поиск проекта по названию\n/sort - сортировка ваших проектов по имени, описанию и приоритету')
@bot.message_handler(commands=['add'])
def add_project(message):
    bot.send_message(message.chat.id, 'Введите название проекта:')
    bot.register_next_step_handler(message, add_description)
def add_description(message):
    global project_name
    project_name = message.text
    bot.send_message(message.chat.id, 'Введите описание проекта:')
    bot.register_next_step_handler(message, prio_project)
def prio_project(message):
    global project_desc
    project_desc = message.text
    bot.send_message(message.chat.id, 'Введите приоритет проекта:')
    bot.register_next_step_handler(message, save_project)
def save_project(message):
    prior = message.text
    user_id = message.chat.id
    c.execute("INSERT INTO projects (name, description, priority, user_id) VALUES (?, ?, ?, ?)", (project_name, project_desc, prior, user_id))
    conn.commit()
    bot.send_message(message.chat.id, 'Проект успешно сохранен!')
@bot.message_handler(commands=['show'])
def showprojects(message):
    user_id = message.chat.id
    bot.send_message(message.chat.id, 'Вот Ваши проекты:')
    projects = c.execute("SELECT name, description, priority FROM Projects WHERE user_id = ?", (user_id,)).fetchall()
    if projects:
        for project in projects:
            bot.send_message(message.chat.id, f'{project[0]} : {project[1]} : {project[2]}')
    else:
        bot.send_message(message.chat.id, 'У Вас пока нет сохраненных проектов.')
@bot.message_handler(commands=['delete'])
def deleteproject(message):
    bot.send_message(message.chat.id, 'Введите название проекта для удаления:')
    bot.register_next_step_handler(message, removeproject)
def removeproject(message):
    projectname = message.text
    user_id = message.chat.id
    c.execute("DELETE FROM Projects WHERE name = ? AND user_id = ?", (projectname, user_id))
    conn.commit()
    bot.send_message(message.chat.id, 'Проект успешно удален!')
@bot.message_handler(commands=['edit'])
def editproject(message):
    bot.send_message(message.chat.id, 'Введите название проекта для редактирования:')
    bot.register_next_step_handler(message, editdescription)
def editdescription(message):
    global projectname
    global user_id
    projectname = message.text
    user_id = message.chat.id
    bot.send_message(message.chat.id, 'Введите новое описание проекта:')
    bot.register_next_step_handler(message, updatepriority)
def updatepriority(message):
    global projectdesc
    projectdesc = message.text
    user_id = message.chat.id
    bot.send_message(message.chat.id, 'Введите новый приоритет проекта (от 1 до 1000):')
    bot.register_next_step_handler(message, updateproject)
def updateproject(message):
    try:
        priority = int(message.text)
        if priority < 1 or priority > 1000:
            bot.send_message(message.chat.id, 'Приоритет должен быть от 1 до 1000.')
            return
        c.execute("UPDATE Projects SET description = ?, priority = ? WHERE name = ? AND user_id = ?", (projectdesc, priority, projectname, user_id))
        conn.commit()
        bot.send_message(message.chat.id, 'Проект успешно отредактирован!')
    except ValueError:
        bot.send_message(message.chat.id, 'Приоритет должен быть числом.')
@bot.message_handler(commands=['save'])
def save_projects(message):
    user_id = message.from_user.id
    c.execute("SELECT name, description, priority FROM projects WHERE user_id = ?", (user_id,))
    projects = c.fetchall()
    with open(f"{user_id}_projects.txt", "w") as file:
        for project in projects:
            file.write(f"Name: {project[0]}\nDescription: {project[1]}\nPriority: {project[2]}\n\n")
        user_id = message.from_user.id
    bot.send_message(message.chat.id, "Проект сохранён в файл!")
    try:
        file_path = f"{user_id}_projects.txt"
        with open(file_path, 'rb') as file:
            bot.send_document(message.chat.id, file)
    except Exception as e:
        bot.send_message(message.chat.id, f"Не получилось отправить файл по причине: {e}")
@bot.message_handler(commands=['find'])
def find_project(message):
    bot.send_message(message.chat.id, "Введите название проекта:")
    bot.register_next_step_handler(message, process_name_step)
def process_name_step(message):
    project_name = message.text
    user_id = message.chat.id
    c.execute("SELECT name, description, priority FROM projects WHERE name=? AND user_id=?", (project_name, user_id))
    project = c.fetchone()
    if project:
        bot.send_message(message.chat.id, f"Название проекта: {project[0]}\nПриоритет: {project[2]}\nОписание: {project[1]}")
    else:
        bot.send_message(message.chat.id, "Проект не найден")
@bot.message_handler(commands=['sort'])
def handle_sort(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, "Как хотите рассортировать? (name, description, priority)")
@bot.message_handler(func=lambda message: True)
def handle_sort_option(message):
    sort_option = message.text.lower()
    user_id = message.from_user.id
    if sort_option not in ['name', 'description', 'priority']:
        bot.send_message(message.chat.id, "Неверный параметр. Попробуйте снова.")
        return
    query = f"SELECT * FROM projects WHERE user_id={user_id} ORDER BY {sort_option}"
    c.execute(query)
    projects = c.fetchall()
    if not projects:
        bot.send_message(message.chat.id, "У вас пока нет проектов.")
    else:
        for project in projects:
            bot.send_message(message.chat.id, f"Название: {project[1]}\nОписание: {project[2]}\nПриоритет: {project[3]}")
bot.polling()
conn.close()