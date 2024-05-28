import subprocess
import shutil
import telebot
import requests
import os
import random
from pydub import AudioSegment
TOKEN = 'private'
bot = telebot.TeleBot(TOKEN)









@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
                 "Привет! Я - бот, который может проговорить любой текст любым голосом.\nПросто отправь мне голосовое сообщение с голосом, которым ты хочешь озвучить текст.")


@bot.message_handler(commands=['recom'])
def send_welcome(message):
    bot.reply_to(message,
                 "Длительность голосового сообщения желательно 7-9 секунд. Убедитесь что в сообщении нет фоновых шумов или музыки, например, во многих фильмах есть тихая музыка, когда многие актеры разговаривают.\nЖелательно чтобы не было никаких больших пауз, пробелов или других звуков.\nУбедитесь, что сообщение не начинается и не заканчивается дышащими звуками (вдох/выдох и т.д.)")



@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message,
                 "1. Отправьте голосовое сообщение в качестве примера для генерации\n(желательно посмотреть рекомендации по записи /recom)\n2. Напишите текст для генерации голосового сообщения. (Не больше 175 символов)\n3. Ожидайте отправки результата")

@bot.message_handler(func=lambda message: message.text == 'Сгенерировать голосовое сообщение')
def handle_help_message(message):
    markup = telebot.types.ReplyKeyboardRemove(selective=False)
    bot.send_message(message.chat.id, 'Отправь голосовое сообщение в качестве примера.\n'
                          'Рекомендации по записи: /recom', reply_markup=markup)




@bot.message_handler(content_types=['voice'])
def handle_voice_message(message):

    user_id = message.from_user.id
    random_ch = random.randint(1, 100000)
    filename = f'{str(user_id)}-{random_ch}'
    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file_path = file_info.file_path
    downloaded_file = bot.download_file(file_path)
    audio_file_name = f'audio_{filename}.ogg'

    with open(audio_file_name, 'wb') as file:
        file.write(downloaded_file)

    subprocess.run(['ffmpeg', '-i', audio_file_name, '-ar', '22050', f'{filename}.wav'])
    os.remove(audio_file_name)

    source_dir = f"{filename}.wav"
    destination_dir = f"/root/speakers/{filename}.wav"
    shutil.move(source_dir, destination_dir)

    bot.send_message(message.chat.id, "Отправь текст, который ты хочешь озвучить выбранным голосом.\n"
                                      "Важно чтобы длина текста не превышала 175 символов.")


    bot.register_next_step_handler(message, handle_text_message, filename)



def handle_text_message(message, filename):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_help = telebot.types.KeyboardButton(text="Сгенерировать голосовое сообщение")
    keyboard.add(button_help)
    text = message.text
    if len(message.text) > 175:
        bot.send_message(message.chat.id, "Ошибка. Текст не должен превышать 175 символов.")
    else:
        mesg = bot.send_message(message.chat.id, 'Добавил в очередь на генерацию голосового сообщения')
        msg = bot.send_sticker(message.chat.id,
                               'CAACAgIAAxkBAAEFnUJmTkkRPRu3jBOeQxpS-No2ccABKgACQwEAAs0bMAiAvonYgQO9kzUE')


        url = 'private'
        params = {
            "text": text,
            "speaker_wav": str(filename),
            "language": "ru"
        }
        res = requests.post(url, json=params)
        if res.status_code == 200:
            output_audio_file_name = f'output_audio_{filename}.wav'
            with open(output_audio_file_name, 'wb') as file:
                file.write(res.content)
            subprocess.run(['ffmpeg', '-i', f'output_audio_{filename}.wav', '-c:a', 'libopus', f'output_audio_{filename}.ogg'])
            output_audio_file_name = f'output_audio_{filename}.ogg'
            voice = open(output_audio_file_name, 'rb')
            bot.send_voice(message.chat.id, voice)
            bot.send_message(message.chat.id,
                             f'Результат генерации по запросу "{text}"', reply_markup=keyboard)
            file.close()
            bot.delete_message(message.chat.id, msg.id)
            bot.delete_message(message.chat.id, mesg.id)
            os.remove(f'/root/speakers/{filename}.wav')


        else:
            print('Error converting text to audio')
            bot.send_message(message.chat.id, 'Ошибка. Попробуйте еще раз или позже.\nРекомендации для записи голосового сообщения - /recom\nИнструкция по использованию - /help')





bot.polling()
