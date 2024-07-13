import asyncio
import logging
import os
import sys
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, BotCommand, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from pytube import YouTube
from pytube.innertube import _default_clients
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from buttons import language_inline_keyboard
from db.config import Base, engine
from db.model import User
from language import data
from state import UserState
from text import start_text, help_text
from utils import format_view, format_duration, format_size

_default_clients["ANDROID_MUSIC"] = _default_clients["ANDROID_CREATOR"]

BOT_TOKEN = getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@dp.message(CommandStart())
async def start_handler(msg: Message, state: FSMContext):
    session = SessionLocal()
    bot_start = BotCommand(command='start', description='Start the bot')
    bot_help = BotCommand(command='help', description='Additional info')
    await msg.bot.set_my_commands([bot_start, bot_help])
    try:
        user = session.query(User).filter(User.telegram_id == msg.from_user.id).first()

        if not user:
            await msg.answer(start_text)
            await state.set_state(UserState.language)
            await msg.answer(text="Tilni tanlang 👇", reply_markup=language_inline_keyboard())
        else:
            await state.set_data(user.__dict__)
            await msg.answer(text=data[user.lang]['ready'])
    finally:
        session.close()


@dp.message(Command('help'))
async def help_command_handler(msg: Message):
    await msg.answer(text=help_text, disable_web_page_preview=True)


@dp.callback_query(lambda c: c.data in ('ENG', 'UZB', 'RUS'))
async def language_handler(callback_query: CallbackQuery, state: FSMContext):
    session = SessionLocal()
    try:
        lang_code = callback_query.data
        state_data = await state.get_data()
        state_data['lang'] = lang_code

        query = select(User).where(User.telegram_id == callback_query.from_user.id)
        result = session.execute(query)
        user = result.fetchone()

        if user:
            user = user[0]
            user.lang = lang_code
            session.commit()
        else:
            new_user = User(
                telegram_id=callback_query.from_user.id,
                lang=lang_code,
                fullname=callback_query.from_user.full_name,
                role="user"
            )
            session.add(new_user)
            session.commit()

        await state.set_data(state_data)
        text = data[lang_code]['greeting']
        await callback_query.answer(text)

        await state.clear()
    finally:
        session.close()


@dp.message()
async def video_url_handler(msg: Message):
    if msg.text.startswith(('https://youtu.be/', 'https://www.youtube.com/')):
        try:
            yt = YouTube(msg.text)
            title = f'🎬 {yt.title}\n'
            views = f'👁 {format_view(yt.views)}\n'
            published_at = f'📥 {str(yt.publish_date)[:10]}\n'
            author = f'👤 {yt.author}\n'
            if 'VEVO' in author:
                author = author[:-5] + '\n'
            length = f'⏳ {format_duration(yt.length)}\n\n'
            addition = 'I can download these tracks:'
            text = title + views + published_at + author + length + addition

            video_streams = yt.streams.filter(file_extension='mp4', only_video=True).desc()
            audio_stream = yt.streams.filter(file_extension='mp4', only_audio=True).first()
            resolutions = [
                [InlineKeyboardButton(
                    text=f'📹{stream.resolution} - {format_size(stream.filesize)}',
                    callback_data=f"{msg.text}|{stream.itag}")]
                for stream in video_streams
            ]
            resolutions.extend(
                [[InlineKeyboardButton(text=f'🔉 Audio - {format_size(audio_stream.filesize)}',
                                       callback_data=f"{msg.text}|{audio_stream.itag}")]])

            resolutions_kb = InlineKeyboardMarkup(inline_keyboard=resolutions)

            await msg.answer_photo(photo=yt.thumbnail_url, caption=text, reply_markup=resolutions_kb)
        except Exception as e:
            await msg.answer(f'An error has occurred: {e}')
    else:
        await msg.answer(text="👻 I can't find the link in your message.\n\nGive me a link 👌")


@dp.callback_query()
async def download_handler(callback_query: CallbackQuery):
    try:
        data = callback_query.data
        if '|' not in data:
            raise ValueError('Invalid callback data format.')

        url, itag = data.rsplit('|', 1)
        await callback_query.answer('Downloading file... Please wait.')
        await youtube_video_downloader(url, callback_query.message, int(itag))
    except Exception as e:
        await callback_query.message.answer(f'An error occurred download_handler: {str(e)}')


async def youtube_video_downloader(url, msg, itag):
    try:
        yt = YouTube(url)
        stream = yt.streams.get_by_itag(itag)

        if stream.filesize > 50 * 1024 * 1024:
            await msg.answer('The file size exceeds the limit allowed by Telegram.')
        else:
            file_path = os.path.join(str(msg.chat.id), stream.default_filename)

            os.makedirs(str(msg.chat.id), exist_ok=True)

            stream.download(output_path=str(msg.chat.id), filename=stream.default_filename)

            input_file = FSInputFile(file_path)

            if stream.type == 'video':
                await msg.answer_video(input_file, caption='@illegal_testing_bot')
            elif stream.type == 'audio':
                await msg.answer_audio(input_file, caption='@illegal_testing_bot')

            os.remove(file_path)
            try:
                os.rmdir(str(msg.chat.id))
            except OSError:
                pass
    except Exception as e:
        await msg.answer(f'An error occurred youtube_video_downloader: {str(e)}')


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    Base.metadata.create_all(engine)
    asyncio.run(main())
