import subprocess
import shutil
import telebot
import requests
import os
import random

TOKEN = '6746624248:AAHpupf3BvhtK3TmH6TE79kEsdMfe2U9GV0'
bot = telebot.TeleBot(TOKEN)









@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
                 "Привет! Я - бот, который может проговорить любой текст любым голосом.\nПросто отправь мне голосовое сообщение с голосом, которым ты хочешь озвучить текст.")


@bot.message_handler(content_types=['voice'])
def handle_voice_message(message):
    user_id = message.from_user.id
    random_ch = random.randint(1, 10000)
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

    bot.send_message(message.chat.id, "Отправь текст, который ты хочешь озвучить выбранным голосом.\n")
    bot.register_next_step_handler(message, handle_text_message, filename)

def handle_text_message(message, filename):
    mesg = bot.send_message(message.chat.id, 'Добавил в очередь на генерацию голосового сообщения')
    msg = bot.send_sticker(message.chat.id,
                           'CAACAgIAAxkBAAEFnUJmTkkRPRu3jBOeQxpS-No2ccABKgACQwEAAs0bMAiAvonYgQO9kzUE')
    text = message.text

    url = 'http://68.183.86.226:8020/tts_to_audio/'
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
        voice = open(output_audio_file_name, 'rb')

        bot.send_voice(message.chat.id, voice)
        bot.send_message(message.chat.id,
                         "Чтобы сгенерировать новую озвучку текста, отправь новое голосовое сообщение в качестве примера.")
        file.close()
        bot.delete_message(message.chat.id, msg.id)
        bot.delete_message(message.chat.id, mesg.id)
        os.remove(f'/root/speakers/{filename}.wav')


    else:
        print('Error converting text to audio')





bot.polling()