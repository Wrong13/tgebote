import aiosqlite
import asyncio

DB_NAME = 'quiz_bot.db'

async def create_table():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS quiz_state (
                user_id INTEGER PRIMARY KEY,
                question_index INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                total_questions INTEGER DEFAULT 0
            )
        ''')
        await db.commit()

async def get_quiz_index(user_id: int) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            'SELECT question_index FROM quiz_state WHERE user_id = ?', 
            (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0

async def update_quiz_index(user_id: int, index: int, is_correct: bool = None):
    async with aiosqlite.connect(DB_NAME) as db:
        if is_correct is not None:
            # Обновляем индекс и статистику
            await db.execute('''
                INSERT INTO quiz_state (user_id, question_index, total_questions, correct_answers)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    question_index = ?,
                    total_questions = total_questions + 1,
                    correct_answers = correct_answers + ?
            ''', (user_id, index, int(is_correct), index, int(is_correct)))
        else:
            # Обновляем только индекс вопроса
            await db.execute('''
                INSERT INTO quiz_state (user_id, question_index)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    question_index = ?
            ''', (user_id, index, index))
        
        await db.commit()

async def get_user_stats(user_id: int) -> tuple[int, int]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            'SELECT correct_answers, total_questions FROM quiz_state WHERE user_id = ?',
            (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result if result else (0, 0)

async def reset_quiz_stats(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT OR REPLACE INTO quiz_state 
            (user_id, question_index, correct_answers, total_questions)
            VALUES (?, 0, 0, 0)
        ''', (user_id,))
        await db.commit()