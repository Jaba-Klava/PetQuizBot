import logging
import random
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_USERNAME = "@kris_mem"

# Список животных и их описаний
ANIMALS = {
   "Амурский тигр": {
        "description": "Вы — сила и благородство! Как амурский тигр, вы уверены в себе.",
        "image": "tiger.jpg"
    },
    "Белый медведь": {
        "description": "Вы выносливы и любите холод! Белый медведь — ваш дух-покровитель.",
        "image": "polar_bear.jpg"
    },
    "Рысь": {
        "description": "Вы загадочны и наблюдательны. Как рысь, предпочитаете действовать наверняка.",
        "image": "lynx.jpg"
    },
    "Снежный барс": {
        "description": "Вы редки и прекрасны. Снежный барс — олицетворение вашей независимости.",
        "image": "snow_leopard.jpg"
    },
    "Манул": {
        "description": "Вы — царь мемов и любитель уюта. Манул с его гримасами — это про вас!",
        "image": "manul.jpg"
    },
    "Фенек": {
        "description": "Вы обаятельны и любите быть в центре внимания, как этот ушастый лис.",
        "image": "fennec.jpg"
    },
    "Сурикат": {
        "description": "Вы общительны и бдительны. Сурикат — ваш тотем!",
        "image": "meerkat.jpg"
    },
    "Китоглав": {
        "description": "Вы философ и немного инопланетянин. Китоглав с его «улыбкой» — ваше тотемное животное!",
        "image": "shoebill.jpg"
    },
    "Жаба ага": {
        "description": "Вы эксцентричны и ядовиты (в хорошем смысле)! Мастер выживания в любых условиях.",
        "image": "toad.jpg"
    },
    "Красная панда": {
        "description": "Вы милы и немного ленивы. Красная панда — ваш пушистый двойник.",
        "image": "red_panda.jpg"
    }
}


# Вопросы викторины
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

# 7658675653:AAFkWmwGFK_D4PoVY3RqG-7MibmpioR0XH8
# Глобальные переменные
user_answers = {}
user_results = {}

def get_main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("Поделиться результатом", callback_data="share_result")],
        [InlineKeyboardButton("Контакты зоопарка", callback_data="zoo_contacts")],
        [InlineKeyboardButton("Оценить бота", callback_data="rate_bot")],
        [InlineKeyboardButton("Пройти ещё раз", callback_data="start_quiz")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_rating_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Не очень", callback_data="rate_1"),
         InlineKeyboardButton("Неплохо", callback_data="rate_2"),
         InlineKeyboardButton("Хорошо", callback_data="rate_3"),
         InlineKeyboardButton("Отлично!", callback_data="rate_4"),
         InlineKeyboardButton("Все супер!", callback_data="rate_5")]
         
    ]
)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! 🐾\n"
        "Ответь на 10 вопросов, и я определю твоё тотемное животное!\n\n"
        "Готов начать?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Начать викторину", callback_data="start_quiz")]
        ])
    )

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_answers[user_id] = []
    user_results[user_id] = None
    await ask_question(query, context, 0)

async def ask_question(query, context: ContextTypes.DEFAULT_TYPE, index: int):
    question = QUIZ_QUESTIONS[index]
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"ans_{index}_{i}")]
        for i, opt in enumerate(question["options"])
    ]
    await query.edit_message_text(
        text=f"Вопрос {index+1}/{len(QUIZ_QUESTIONS)}:\n{question['question']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    _, q_idx, a_idx = query.data.split('_')
    q_idx, a_idx = int(q_idx), int(a_idx)
    
    user_id = query.from_user.id
    if user_id not in user_answers:
        user_answers[user_id] = []
    user_answers[user_id].append((q_idx, a_idx))
    
    if q_idx + 1 < len(QUIZ_QUESTIONS):
        await ask_question(query, context, q_idx + 1)
    else:
        await show_result(query, context, user_id)

async def show_result(query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    # Упрощенный расчет результата
    result_animal = random.choice(list(ANIMALS.keys()))
    description = ANIMALS[result_animal]['description']
    user_results[user_id] = result_animal
    
    # Отправляем результат с фото
    with open(f"images/{ANIMALS[result_animal]['image']}", 'rb') as photo:
        await context.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=photo,
            caption=f"🎉 Твоё тотемное животное — {result_animal}!\n\n{description}"
        )
    
    # Отправляем меню отдельным сообщением
    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text="Что вы хотите сделать дальше?",
        reply_markup=get_main_menu_keyboard())
    

async def share_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in user_results:
        result_animal = user_results[user_id]
        description = ANIMALS[result_animal]['description']
        
        share_text = (
            f"🐾 Я прошёл викторину и мое тотемное животное — {result_animal}!\n\n"
            f"{description}\n\n"
            "Попробуй и ты: @PetQuizBot"
        )
        
        await query.edit_message_text(
            text=f"{share_text}\n\nСкопируй этот текст и поделись с друзьями!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Назад", callback_data="back_to_result")]
            ])
        )

async def back_to_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text="Что вы хотите сделать дальше?",
        reply_markup=get_main_menu_keyboard())
    

async def zoo_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="🐾 Контакты Московского зоопарка:\n\n"
        "📞 Телефон: 7 (962) 971-38-75\n"
        "✉️ zoofriends@moscowzoo.ru\n\n"
        "По вопросам работы бота пишите @kris_mem",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("← Назад", callback_data="back_to_result")]
        ])
    )

async def rate_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="Пожалуйста, оцените работу бота:",
        reply_markup=get_rating_keyboard())
    reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("← Назад", callback_data="back_to_result")]
        ])

async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    rating = int(query.data.split('_')[1])
    user = query.from_user
    
    # Отправляем оценку администратору
    await context.bot.send_message(
        chat_id=ADMIN_USERNAME,
        text=f"⭐ Новая оценка бота от @{user.username}: {rating}/5"
    )
    
    await query.edit_message_text(
        text="Спасибо за вашу оценку!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("← Назад", callback_data="back_to_result")]
        ])
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_quiz":
        await start_quiz(update, context)
    elif query.data.startswith("ans_"):
        await handle_answer(update, context)
    elif query.data == "share_result":
        await share_result(update, context)
    elif query.data == "zoo_contacts":
        await zoo_contacts(update, context)
    elif query.data == "rate_bot":
        await rate_bot(update, context)
    elif query.data.startswith("rate_"):
        await handle_rating(update, context)
    elif query.data == "back_to_result":
        await back_to_result(update, context)

def main():
    application = Application.builder().token("7658675653:AAFkWmwGFK_D4PoVY3RqG-7MibmpioR0XH8").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    application.run_polling()

if __name__ == '__main__':
    main()