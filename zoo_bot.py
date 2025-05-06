import logging
import random
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    MessageHandler,
    filters
)

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Список животных и их описаний
ANIMALS = {
    "Амурский тигр": {
        "description": "Вы — сила и благородство! Как амурский тигр, вы уверены в себе.",
    },
    "Белый медведь": {
        "description": "Вы выносливы и любите холод! Белый медведь — ваш дух-покровитель.",
    },
    "Рысь": {
        "description": "Вы загадочны и наблюдательны. Как рысь, предпочитаете действовать наверняка.",
    },
    "Снежный барс": {
        "description": "Вы редки и прекрасны. Снежный барс — олицетворение вашей независимости.",
    },
    "Манул": {
        "description": "Вы — царь мемов и любитель уюта. Манул с его гримасами — это про вас!",
    },
    "Фенек": {
        "description": "Вы обаятельны и любите быть в центре внимания, как этот ушастый лис.",
    },
    "Сурикат": {
        "description": "Вы общительны и бдительны. Сурикат — ваш тотем!",
    },
    "Китоглав": {
        "description": "Вы философ и немного инопланетянин. Китоглав с его «улыбкой» — ваше тотемное животное!",
    },
    "Жаба ага": {
        "description": "Вы эксцентричны и ядовиты (в хорошем смысле)! Мастер выживания в любых условиях.",
        "image": "zhaba.jpg"
    },
    "Красная панда": {
        "description": "Вы милы и немного ленивы. Красная панда — ваш пушистый двойник.",
    }
}

# 10 сбалансированных вопросов
QUIZ_QUESTIONS = [
    {
        "question": "Какой климат вам комфортнее?",
        "options": ["Арктический холод", "Тропическая влажность", "Умеренный", "Жаркий сухой"],
        "weights": {
            "Белый медведь": 1,
            "Рысь": 2,
            "Красная панда": 3,
            "Фенек": 1,
            "special": {1: {"Жаба ага": 5}}  # Второй вариант -> жаба
        }
    },
    {
        "question": "Как вы реагируете на опасность?",
        "options": ["Атака", "Маскировка", "Бегство", "Ядовитое выделение"],
        "weights": {
            "Амурский тигр": 1,
            "Снежный барс": 2,
            "Мышь-малютка": 3,
            "special": {3: {"Жаба ага": 5}}  # Четвертый вариант -> жаба
        }
    },
    {
        "question": "Ваш стиль общения?",
        "options": ["Доминирующий", "Загадочный", "Дружелюбный", "Токсичный"],
        "weights": {
            "Амурский тигр": 1,
            "Китоглав": 2,
            "Сурикат": 3,
            "special": {3: {"Жаба ага": 5}}  # Четвертый вариант -> жаба
        }
    },
    {
        "question": "Где вы предпочитаете жить?",
        "options": ["Ледяные пустыни", "Болота", "Горные вершины", "Леса"],
        "weights": {
            "Белый медведь": 1,
            "Манул": 2,
            "Рысь": 3,
            "special": {1: {"Жаба ага": 5}}  # Второй вариант -> жаба
        }
    },
    {
        "question": "Как вы принимаете решения?",
        "options": ["Быстро и решительно", "Осторожно", "После раздумий", "Советуюсь с другими"],
        "weights": {
            "Амурский тигр": 1,
            "Снежный барс": 2,
            "Китоглав": 3,
            "special": {}  # Нет специальных баллов
        }
    },
    {
        "question": "Ваше любимое время суток?",
        "options": ["Рассвет", "День", "Сумерки", "Ночь"],
        "weights": {
            "Фенек": 1,
            "Красная панда": 2,
            "Манул": 3,
            "special": {}  # Нет специальных баллов
        }
    },
    {
        "question": "Как вы относитесь к риску?",
        "options": ["Обожаю риск", "Рассчитываю варианты", "Избегаю риска", "Рискую с подстраховкой"],
        "weights": {
            "Амурский тигр": 1,
            "Рысь": 2,
            "Красная панда": 3,
            "special": {}  # Нет специальных баллов
        }
    },
    {
        "question": "Ваш подход к проблемам?",
        "options": ["Лобовая атака", "Хитрость", "Избегание", "Поиск помощи"],
        "weights": {
            "Белый медведь": 1,
            "Снежный барс": 2,
            "Сурикат": 3,
            "special": {}  # Нет специальных баллов
        }
    },
    {
        "question": "Что для вас важнее?",
        "options": ["Сила", "Безопасность", "Знания", "Комфорт"],
        "weights": {
            "Амурский тигр": 1,
            "Манул": 2,
            "Китоглав": 3,
            "special": {}  # Нет специальных баллов
        }
    },
    {
        "question": "Как вы ведете себя в компании?",
        "options": ["Лидер", "Наблюдатель", "Душа компании", "Одиночка"],
        "weights": {
            "Сурикат": 1,
            "Рысь": 2,
            "Фенек": 3,
            "special": {}  # Нет специальных баллов
        }
    }
]

user_answers = {}

async def start(update: Update, context: CallbackContext) -> None:
    """Приветствие и начало викторины"""
    user = update.message.from_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! 🐾\n"
        "Ответь на 10 вопросов, и я определю твоё тотемное животное!\n\n"
        "Готов начать?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Начать викторину", callback_data="start_quiz")]
        ])
    )

async def start_quiz(update: Update, context: CallbackContext) -> None:
    """Начало викторины"""
    query = update.callback_query
    await query.answer()
    user_answers[query.from_user.id] = []
    await ask_question(update, context, 0)

async def ask_question(update: Update, context: CallbackContext, index: int) -> None:
    """Задаёт вопрос с вариантами"""
    question = QUIZ_QUESTIONS[index]
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"ans_{index}_{i}")]
        for i, opt in enumerate(question["options"])
    ]
    
    await update.callback_query.edit_message_text(
        text=f"Вопрос {index+1}/{len(QUIZ_QUESTIONS)}:\n{question['question']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_answer(update: Update, context: CallbackContext) -> None:
    """Обработка ответа"""
    query = update.callback_query
    await query.answer()
    
    _, q_idx, a_idx = query.data.split('_')
    q_idx, a_idx = int(q_idx), int(a_idx)
    
    user_id = query.from_user.id
    if user_id not in user_answers:
        user_answers[user_id] = []
    user_answers[user_id].append((q_idx, a_idx))
    
    if q_idx + 1 < len(QUIZ_QUESTIONS):
        await ask_question(update, context, q_idx + 1)
    else:
        await show_result(update, context, user_id)

async def show_result(update: Update, context: CallbackContext, user_id: int) -> None:
    """Определение результата с новым алгоритмом"""
    animal_scores = defaultdict(int)
    jaba_points = 0
    
    for q_idx, a_idx in user_answers[user_id]:
        question = QUIZ_QUESTIONS[q_idx]
        
        # Основные баллы
        for animal, weight in question['weights'].items():
            if animal != 'special':
                animal_scores[animal] += weight
        
        # Специальные баллы для жабы
        if 'special' in question['weights'] and a_idx in question['weights']['special']:
            jaba_points += question['weights']['special'][a_idx].get('Жаба ага', 0)
    
    # Жаба побеждает только при достаточном количестве специальных баллов
    if jaba_points >= 15:  # 3+ "жабьих" ответа
        result_animal = 'Жаба ага'
    else:
        # Удаляем жабу из общего подсчета
        animal_scores.pop('Жаба ага', None)
        
        # Выбираем случайно из топ-3 животных
        top_animals = sorted(animal_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        result_animal = random.choice(top_animals)[0] if top_animals else 'Манул'
    
    description = ANIMALS[result_animal]['description']
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Узнать о программе", callback_data="about_program")],
        [InlineKeyboardButton("Пройти ещё раз", callback_data="start_quiz")]
    ])

    # Отправка фото для жабы
    if result_animal == 'Жаба ага' and 'image' in ANIMALS[result_animal]:
        try:
            with open(ANIMALS[result_animal]['image'], 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=update.callback_query.message.chat.id,
                    photo=photo,
                    caption=f"🎉 Твоё тотемное животное — {result_animal}!\n\n{description}",
                    reply_markup=keyboard
                )
        except FileNotFoundError:
            await send_text_result(update, result_animal, description, keyboard)
    else:
        await send_text_result(update, result_animal, description, keyboard)

async def send_text_result(update: Update, animal: str, desc: str, keyboard) -> None:
    """Отправляет текстовый результат"""
    await update.callback_query.edit_message_text(
        text=f"🎉 Твоё тотемное животное — {animal}!\n\n{desc}",
        reply_markup=keyboard
    )

async def about_program(update: Update, context: CallbackContext) -> None:
    """Информация о программе опеки"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="🐾 Программа опеки над животными\n\n"
        "Вы можете стать опекуном выбранного животного в Московском зоопарке!\n\n"
        "Контакты:\n"
        "📞 +7 (962) 971-38-75\n"
        "✉️ zoofriends@moscowzoo.ru",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("На главную", callback_data="start_quiz")]
        ])
    )

def main() -> None:
    """Запуск бота"""
    application = Application.builder().token("7658675653:AAFkWmwGFK_D4PoVY3RqG-7MibmpioR0XH8").build()
    
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(start_quiz, pattern="^start_quiz$"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^ans_"))
    application.add_handler(CallbackQueryHandler(about_program, pattern="^about_program$"))
    
    application.run_polling()

if __name__ == '__main__':
    main()