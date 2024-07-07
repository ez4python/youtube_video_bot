import asyncio
import logging
import os
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile, BotCommand
from dotenv import load_dotenv
from pytube import YouTube
from pytube.innertube import _default_clients

from translations import help_text
from utils import format_view, format_duration, format_size

_default_clients["ANDROID_MUSIC"] = _default_clients["ANDROID_CREATOR"]

load_dotenv()
TOKEN = getenv('BOT_TOKEN')

dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@dp.message(CommandStart())
async def command_start_handler(msg: Message) -> None:
    start = BotCommand(command='start', description='Start the bot')
    help = BotCommand(command='help', description='Additional info')
    await msg.bot.set_my_commands([start, help])
    await msg.answer_(f"Hello, {html.bold(msg.from_user.full_name)}!")


@dp.message(Command('help'))
async def help_command_handler(msg: Message):
    await msg.answer(text=help_text)


@dp.message()
async def video_url_handler(msg: Message) -> None:
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
            addition = 'I can download these tracks:\n\n'
            text = title + views + published_at + author + length + addition

            video_streams = yt.streams.filter(only_video=True, file_extension='mp4')
            audio_streams = yt.streams.filter(only_audio=True, file_extension='mp4')
            resolutions = [
                [InlineKeyboardButton(
                    text=f'📹{stream.resolution} - {format_size(stream.filesize)}',
                    callback_data=f"{msg.text}|{stream.itag}")]
                for stream in video_streams[::-1]
            ]
            resolutions.extend([
                [InlineKeyboardButton(
                    text=f'🔉 Audio - {format_size(stream.filesize)}',
                    callback_data=f"{msg.text}|{stream.itag}")]
                for stream in audio_streams
            ])

            resolutions_kb = InlineKeyboardMarkup(inline_keyboard=resolutions)

            await msg.answer_photo(photo=yt.thumbnail_url, caption=text, reply_markup=resolutions_kb)
        except Exception as e:
            await msg.answer(f'An error occurred: {str(e)}')
    else:
        await msg.answer(text="👻 I can't find the link in your message.\n\nGive me a link 👌")


@dp.callback_query()
async def download_handler(callback_query: CallbackQuery) -> None:
    try:
        data = callback_query.data
        if '|' not in data:
            raise ValueError('Invalid callback data format.')

        url, itag = data.rsplit('|', 1)  # Split only on the last '|'
        await callback_query.answer('Downloading file... Please wait.')
        await youtube_video_downloader(url, callback_query.message, int(itag))
    except Exception as e:
        await callback_query.message.answer(f'An error occurred: {str(e)}')


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
                await bot.send_video(msg.chat.id, input_file, caption='*This is your video*', parse_mode='Markdown')
                await msg.answer_video()
            elif stream.type == 'audio':
                await bot.send_audio(msg.chat.id, input_file, caption='*This is your audio*', parse_mode='Markdown')

            os.remove(file_path)
            try:
                os.rmdir(str(msg.chat.id))
            except OSError:
                pass
    except Exception as e:
        await msg.answer(f'An error occurred: {str(e)}')


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
