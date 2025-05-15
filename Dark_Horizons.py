import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio

# Включение логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Вопросы викторины
from resources import QUIZZES

# Хранение информации о пользователях
user_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало работы бота."""
    keyboard = [
        [InlineKeyboardButton("Общие знания по книге", callback_data='Общие знания по книге')],
        [InlineKeyboardButton("Углубленные знания", callback_data='Углубленные знания')],
        [InlineKeyboardButton("Уилл и Маркус", callback_data='Уилл и Маркус')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите тему викторины:', reply_markup=reply_markup)


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запуск викторины по выбранной теме."""
    query = update.callback_query
    await query.answer()
    topic = query.data

    # Инициализация данных пользователя, если их нет
    if query.from_user.id not in user_data:
        user_data[query.from_user.id] = {}

    if topic in user_data[query.from_user.id]:
        await query.edit_message_text(text="Вы уже прошли эту викторину.")
        return

    user_data[query.from_user.id][topic] = {'current_question': 0, 'score': 0}
    await ask_question(query, topic)


async def ask_question(query, topic):
    """Задать вопрос текущему пользователю."""
    user_info = user_data[query.from_user.id][topic]
    question_index = user_info['current_question']

    if question_index < len(QUIZZES[topic]):
        question_data = QUIZZES[topic][question_index]
        question_text = question_data["question"]
        options = question_data["options"]

        keyboard = [[InlineKeyboardButton(option.ljust(20), callback_data=str(idx))] for idx, option in
                    enumerate(options)]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text=question_text, reply_markup=reply_markup)
    else:
        score = user_info['score']
        total_questions = len(QUIZZES[topic])

        # Определение категории на основе набранных баллов с учетом общего количества вопросов
        category = evaluate_score(score, total_questions)

        # Завершение викторины
        await query.edit_message_text(
            text=f"Викторина завершена! Ваш результат: {score} из {total_questions} \n{category}")

        # Удалите данные пользователю для данной викторины
        del user_data[query.from_user.id][topic]  # Очистка данных по викторине

def evaluate_score(score, total_questions):
    """Оценка результата викторины, добавление 10 категорий."""
    percentage = score / total_questions

    if percentage <= 0.1:
        return "Салли сжимает кулаки. Вы ему не нравитесь. Ваши знания оставляют желать лучшего."
    elif percentage <= 0.2:
        return "Себастьян Ашер потирает руки. С такими знаниями вы станете легкой добычей в 'Биохроме'!"
    elif percentage <= 0.3:
        return "Я уверен, ты можешь лучше! Соберись! (С)Салли Браун"
    elif percentage <= 0.4:
        return "Неплохо. Во Внешних землях вы протянули бы... пару недель."
    elif percentage <= 0.5:
        return "Весьма неплохо! С таким багажом знаний вы одолеете любого мутанта!"
    elif percentage <= 0.6:
        return "Впечатляет! Знаний достаточно, чтобы выжить в 'Биохроме'."
    elif percentage <= 0.7:
        return "Волчья стая даже пробовать не станет. Вы серьезный противник, в пустыне вас не догнать!"
    elif percentage <= 0.8:
        return "Питер молча хлопает вам. С такими знаниями вы станете важной частью команды!"
    elif percentage <= 0.9:
        return "Гениально! Вы точно не обладаете ученой степень по постапокалипсису?"
    else:
        return "Вы - ходячая энциклопедия. Даже Маркус знает меньше!"




async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ответа пользователя на вопрос викторины."""
    query = update.callback_query
    await query.answer()

    # Определение темы, для которой идет викторина
    topic = next((t for t, data in user_data[query.from_user.id].items() if 'current_question' in data), None)
    if topic is None:
        await query.edit_message_text(text="Викторина не найдена.")
        return

    question_index = user_data[query.from_user.id][topic]['current_question']
    question_data = QUIZZES[topic][question_index]

    # Проверка ответа
    if int(query.data) == question_data['answer']:
        user_data[query.from_user.id][topic]['score'] += 1
        response_message = "Правильно! 🎉"
    else:
        correct_answer_text = question_data['options'][question_data['answer']]
        response_message = f"Неправильно. Правильный ответ: {correct_answer_text}. ❌"

        # Отправка пользователя сообщения о результатах ответа
    await query.edit_message_text(text=response_message)

        # Задержка перед переходом к следующему вопросу
    # await asyncio.sleep(5)

    # Увеличение индекса текущего вопроса
    user_data[query.from_user.id][topic]['current_question'] += 1

    # Задайте следующий вопрос после небольшого интервала
    await ask_question(query, topic)


def main():
    """Запуск бота."""
    application = ApplicationBuilder().token("7316829856:AAESMx7FVGWkqyqRtSemsMo-2JZDMZv4-JQ").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(quiz, pattern="^Общие знания по книге$"))
    application.add_handler(CallbackQueryHandler(quiz, pattern="^Углубленные знания$"))
    application.add_handler(CallbackQueryHandler(quiz, pattern="^Уилл и Маркус$"))
    application.add_handler(CallbackQueryHandler(answer, pattern=r'^\d+$'))

    # Запускаем бота с помощью метода run_polling(), который будет работать с асинхронными функциями.
    application.run_polling()


if __name__ == '__main__':
    main()
