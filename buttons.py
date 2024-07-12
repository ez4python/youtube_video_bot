from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def language_inline_keyboard():
    uzb = InlineKeyboardButton(text='🇺🇿 UZB', callback_data='UZB')
    eng = InlineKeyboardButton(text='🇬🇧 ENG', callback_data='ENG')
    rus = InlineKeyboardButton(text='🇷🇺 RUS', callback_data='RUS')
    design = [[uzb, eng, rus]]
    return InlineKeyboardMarkup(inline_keyboard=design)
