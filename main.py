from aiogram import Bot, Dispatcher, executor, types
import hidden_user_data
import constants
import common_vars
from models_processing import prepare_models, get_models_predictions

bot = Bot(token=hidden_user_data.CHAT_BOT_API_TOKEN)
dsp = Dispatcher(bot)
current_test_status = False
current_test_question_number = -1
common_rating = []
user_answers = []


@dsp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    kb = [
       [
           types.KeyboardButton(text=constants.START_TEST_BUTTON_TEXT),
       ],
    ]

    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

    message_text = ""
    message_text += "Привет, я *PsyChatBot*!\n"
    message_text += "Провожу тестирование и понимаю письменную человеческую речь. "
    message_text += "Вы готовы попробовать и пройти тест?\n"
    message_text += "\n"
    message_text += "/help - подсказка\n"

    await message.reply(message_text, reply_markup=keyboard, parse_mode="Markdown")
    print("Отправлено приветственное сообщение.")


@dsp.message_handler()
async def get_text_messages(message: types.Message):
    global current_test_question_number, current_test_status, common_rating, user_answers
    message_text = ""
    income_message_in_lower = message.text.lower()
    if current_test_status:
        if income_message_in_lower in (list(constants.ALL_COMMANDS.values()) + [constants.START_TEST_BUTTON_TEXT.lower()]):
            if income_message_in_lower == constants.ALL_COMMANDS["stoptest"]:
                current_test_status = False
                common_rating = []
                user_answers = []
                print("-----------------------------")
                print("Тестирование прервано.")
                print("Перешли в состояние: Общение.")
                message_text += "*Тестирование прервано*!"
                await message.answer(message_text, parse_mode="Markdown")

                return
            else:
                message_text += "В данный момент Вы проходите тестирование. "
                message_text += "В это время поддерживаются только команда /stoptest \n\n"
                message_text += "Пожалуйста, продолжите предложение:\n"
                message_text += common_vars.TEST_QUESTIONS[current_test_question_number - 1]
                await message.answer(message_text, parse_mode="Markdown")

                return

        user_answers = user_answers + [message.text]
        curr_rating_list = get_models_predictions(common_vars.TEST_QUESTIONS[current_test_question_number - 1], income_message_in_lower)
        common_rating += [curr_rating_list]
        print("Дан ответ:", message.text, "|  Дана оценка:", curr_rating_list)
        if len(common_vars.TEST_QUESTIONS) == current_test_question_number:
            # Закончились вопросы. Останавливаем опрос.
            current_test_status = False
            print("-----------------------------")
            print("Перешли в состояние: Общение.")
            message_text += "*Тестирование завершено*!\n"
            message_text += "\n"
            message_text += "Оценка ответов производилась на предмет твоей мотивации по четырём направлениям. "
            message_text += "Получены следующие результаты:\n"
            await message.answer(message_text, parse_mode="Markdown")

            for num_test in [1, 2, 3, 4]:
                total = get_result_for_test(num_test, common_rating)
                result = round(total / len(common_vars.TEST_QUESTIONS), 2)
                message_text = ""
                message_text += f"*{num_test}*. {constants.SUB_TEST_TYPES[num_test]}\n"
                message_text += f"-----------------------\n"
                message_text += f"*Набрано баллов*: {total}\n*Оценка*: {result}\n*Вывод*: {translate_result(result)}"
                await message.answer(message_text, parse_mode="Markdown")

        else:
            await message.answer(common_vars.TEST_QUESTIONS[current_test_question_number], parse_mode="Markdown")

            current_test_question_number += 1
            print(f"Статус: Тестирование. Задан вопрос №{current_test_question_number}")
    else:
        if "привет" in income_message_in_lower:
            await message.answer("*Привет*, чем я могу тебе помочь?", parse_mode="Markdown")
        elif income_message_in_lower in ["/test", constants.START_TEST_BUTTON_TEXT.lower()]:
            message_text += "*Начинаем тестирование*!\n"
            message_text += "\n"
            message_text += "Я буду давать тебе начало предложений.\n"
            message_text += "Твоя задача будет продолжить эти предложения.\n"
            message_text += "Ставить в конце точку не обязательно.\n"
            message_text += "Просто отправь мне твой вариант завершения.\n"
            message_text += "\n"
            message_text += "Например:\n"
            message_text += "*Предложение*: Новый компьютер, это тот...\n"
            message_text += "*Продолжение*: у которого современный процессор"
            await message.answer(message_text, parse_mode="Markdown")
            await message.answer(f"*Начинаем*. Всего предложений *{len(common_vars.TEST_QUESTIONS)}* шт.\nОтвечай сразу после появления следующего текста.", parse_mode="Markdown")
            await message.answer(common_vars.TEST_QUESTIONS[0])
            current_test_status = True
            common_rating = []
            user_answers = []
            print("-----------------------------")
            print("Перешли в состояние: Тестирование.")
            current_test_question_number = 1
            print(f"Статус: Тестирование. Задан вопрос №{current_test_question_number}")

        elif income_message_in_lower == "/stoptest":
            message_text += "Эта команда срабатывает только в процессе прохождения тестирования."
            await message.answer(message_text, parse_mode="Markdown")

        elif income_message_in_lower == "/help":
            message_text += "Этот бот предназначен для тестирования по методике *М.Ньюттена* "
            message_text += "«Неоконченные предложения» в модификации *А.Б.Орлова*.\n\n"
            message_text += "*Цель*: диагностика мотивации учения у школьника.\n"
            message_text += "*Порядок исследования*: я показываю начало предложения "
            message_text += "а ты должен напечатать и отправить то как думаешь оно должно оканчиваться.\n\n"
            message_text += "Поддерживаются команды:\n"
            message_text += "/help (подсказка)\n"
            message_text += "/test (тестирование)\n"
            message_text += "/stoptest (прекратить)\n"
            message_text += "/stat (статистика)\n"
            await message.answer(message_text, parse_mode="Markdown")

        elif income_message_in_lower == "/stat":
            if len(common_rating) != len(common_vars.TEST_QUESTIONS):
                await message.answer("Статистика по последнему тестированию отсутствует.")
            else:
                await message.answer("*Статистика по последнему тестированию*:", parse_mode="Markdown")
                for num in range(len(common_vars.TEST_QUESTIONS)):
                    await message.answer(f"{common_vars.TEST_QUESTIONS[num]} {user_answers[num]}\n*{common_rating[num]}*", parse_mode="Markdown")

        else:
            message_text += "Мои способности по распознаванию письменной человеческой речи "
            message_text += "включаются только в процессе тестирования, поэтому сейчас я тебя не понимаю!\n"
            message_text += "\n"
            message_text += "Выбери или напиши одно из трёх:\n"
            message_text += "/help (подсказка)\n"
            message_text += "/test (тестирование)\n"
            message_text += "/stat (статистика)"
            await message.answer(message_text, parse_mode="Markdown")


def translate_result(result):
    # Оценивание производится исходя из гипотезы, что
    # 1. Школьник может набрать по каждому из типов тестов один балл
    # 2. Если школьник набрал:
    # 2.1. от 0.3 - высоко мотивирован;
    # 2.2. от 0.1 до 0.3 - просто мотивирован;
    # 2.3. от -0.1 до 0.1 - не мотивирован;
    # 2.4. от -0.3 до -0.1 он демотивирован;
    # 2.5. ниже -0.3 - сильно демотивирован.

    if result > 0.3:
        return "Высокая мотивация"
    if result > 0.1:
        return "Мотивирован"
    if result > -0.1:
        return "Отсутствует мотивация"
    if result > -0.3:
        return "Демотивирован"

    return "Крайне сильно демотивирован"


def get_result_for_test(num_test, ratings):
    sum_box = 0
    for one_rating in ratings:
        sum_box += one_rating[num_test - 1]

    return sum_box


if __name__ == '__main__':
    prepare_models()
    print("Запускаем бота.")
    print("Состояние: Готовность к общению.")
    executor.start_polling(dsp)
