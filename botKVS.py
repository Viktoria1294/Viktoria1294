import nest_asyncio
nest_asyncio.apply()
import aiosqlite
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
API_TOKEN = '8062258818:AAHrXPXLyBG6JsbVRgMYouDlGnErEThzWZk'

# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()

# Формирую базу данных
DB_Chem = 'quize_chem.db'

# Словарь квиза
chem_data = [{'question': 'Что такое качественные реакции?',
              'options': ['Необратимые реакции', 'Дают визуальный ответ на возможный состав веществ',
                          'В результате всегда выделяется газ', 'Реакции со сложными веществами'],
              'correct_option': 1},
             {'question': 'Качественной реакцией на одноатомные спирты является взаимодействие с?',
              'options': ['Гидроксидом меди', 'Бромной водой',
                          'Оксидом меди', 'Гидроксидом натрия'],
              'correct_option': 0},
             {'question': 'Качественной реакцией на алкины является взаимодействие с?',
              'options': ['Окисдом меди', 'Оксидом серебра в аммиачном растворе',
                          'Хлоридом желаза III', 'Азотистой кислотой'],
              'correct_option': 1},
             {'question': 'Что образуется в результате взаимодействия ацетальдегида с гадроксидом меди?',
              'options': ['Фиолетовый раствор', 'Белый осадок', 
                          'Голубой раствор', 'Красный осадок'],
              'correct_option': 3},
             {'question': 'Что образуется в результате взаимодействия фенола с бромной водой?',
              'options': ['Белый осадок', 'Обесцвечивание раствора',
                          'Признаков нет', 'Выделяется газ'],
              'correct_option': 0},
             {'question': 'Выберите ответ, в котором оба класса веществ реагируют с перманганатом калия?',
              'options': ['Алканы и алкены', 'Бензол и его гомологи',
                          'Альдегиды и спирты', 'Альдегиды и карб. кислоты'],
              'correct_option': 2},
             {'question': 'Качественную реакцию "Серебрянное зеркало" имеют?',
              'options': ['Алкины', 'Арены',
                          'Альдегиды', 'Кислоты'],
              'correct_option': 2},
             {'question': 'Какие амины не вступают в  реакцию с азотистой кислотой?',
              'options': ['Первичные', 'Вторичные',
                          'Третичные', 'Ароматические'],
              'correct_option': 2},
             {'question': 'Какой класс веществ вступает в реакцию с активными металлами ?',
              'options': ['Алкены', 'Арены',
                          'Амины', 'Алкины'],
              'correct_option': 3},
             {'question': 'Чем отличить глицерин от формальдегида?',
              'options': ['Гидроксидом меди', 'Перманганатом калия',
                          'Оксидом меди', 'Дихроматом натрия'],
              'correct_option': 0}]


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer("Добро пожаловать в квиз!", reply_markup = builder.as_markup(resize_keyboard=True))

async def create_table():
    # Создаем соединение с базой данных
    async with aiosqlite.connect(DB_Chem) as db:
        # Создаем таблицу
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER)''')
        # Сохраняем изменения
        await db.commit()

async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)

    await get_question(message, user_id)

async def get_question(message, user_id):

    # Запрашиваем из базы текущий индекс для вопроса
    current_question_index = await get_quiz_index(user_id)
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = chem_data[current_question_index]['correct_option']
    opts = chem_data[current_question_index]['options']
    kb = generate_option_keyboard(opts, opts[correct_index])
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer(f"{chem_data[current_question_index]['question']}", reply_markup=kb)

def generate_option_keyboard(answer_options, right_answer):
  builder = InlineKeyboardBuilder()

  for option in answer_options:
      builder.add(types.InlineKeyboardButton(
          text = option,
          callback_data = "right_answer" if option == right_answer else "wrong_answer"))

  builder.adjust(1)
  return builder.as_markup()

@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):

    await callback.bot.edit_message_reply_markup(
        chat_id = callback.from_user.id,
        message_id = callback.message.message_id,
        reply_markup = None)

    await callback.message.answer("Верно!")
    current_question_index = await get_quiz_index(callback.from_user.id)
    current_question_index = current_question_index + 1
    await update_quiz_index(callback.from_user.id, current_question_index)


    if current_question_index < len(chem_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )


    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = chem_data[current_question_index]['correct_option']

    await callback.message.answer(f"Неправильно. Правильный ответ: {chem_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index = current_question_index + 1
    await update_quiz_index(callback.from_user.id, current_question_index)


    if current_question_index < len(chem_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


async def get_quiz_index(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_Chem) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0

async def update_quiz_index(user_id, index):
    # Создаем соединение с базой данных
    async with aiosqlite.connect(DB_Chem) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index) VALUES (?, ?)', (user_id, index))
        # Сохраняем изменения
        await db.commit()

# Хэндлер на команду /quiz
@dp.message(F.text == "Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):

    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)


# Запуск процесса поллинга новых апдейтов
async def main():

    # Запускаем создание таблицы базы данных
    await create_table()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())