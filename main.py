#@title Полный код бота для самоконтроля
import aiosqlite
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
import databaze
import logicca

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Замените "YOUR_BOT_TOKEN" на токен, который вы получили от BotFather
API_TOKEN = '1462254374:AAFyKg3xtOYwlyj4LBTrhNiIF3c99c0CIkE'

# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    #builder = ReplyKeyboardBuilder()
    kb = [
        [types.KeyboardButton(text="Начать игру")],
        [types.KeyboardButton(text="Статистика")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await message.answer("Добро пожаловать в квиз!", reply_markup=keyboard)


@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await databaze.get_quiz_index(callback.from_user.id)
    correct_option = logicca.quiz_data[current_question_index]['correct_option']

    await callback.message.answer(f"Неправильно. Правильный ответ: {logicca.quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await databaze.update_quiz_index(callback.from_user.id, current_question_index,is_correct=False)


    if current_question_index < len(logicca.quiz_data):
        await logicca.get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")

@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):

    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    await callback.message.answer("Верно!")
    current_question_index = await databaze.get_quiz_index(callback.from_user.id)
    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await databaze.update_quiz_index(callback.from_user.id, current_question_index,is_correct=True)


    if current_question_index < len(logicca.quiz_data):
        await logicca.get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")







# Хэндлер на команду /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):

    await message.answer(f"Давайте начнем квиз!")
    await logicca.new_quiz(message)

@dp.message(F.text=="Статистика")
@dp.message(Command("stat"))
async def get_stat(message: types.Message):
    correct, total = await databaze.get_user_stats(message.from_user.id)    
    stats_text = (
        f"📊 Ваша статистика:\n"
        f"✅ Правильных ответов: {correct}\n"
        f"❌ Всего вопросов: {total}\n"
        f"🏆 Процент правильных: {correct/total*100:.1f}%" if total > 0 else "0%"
    )
    
    await message.answer(stats_text)


async def main():

    # Запускаем создание таблицы базы данных
    await databaze.create_table()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())