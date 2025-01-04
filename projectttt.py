import subprocess
import shutil
import telebot
import requests
import os
import random
import traceback


TOKEN = "'
bot = telebot.TeleBot(TOKEN)
admin_id = 634028449

keyboard1 = telebot.types.InlineKeyboardMarkup()
keyboard2 = telebot.types.InlineKeyboardMarkup()
button_help = telebot.types.InlineKeyboardButton(text="\U00002705 Понятно",
                                                     callback_data='delete_help')
button_recom = telebot.types.InlineKeyboardButton(text="\U00002705 Понятно",
                                                     callback_data='delete_recom')
keyboard1.add(button_help)
keyboard2.add(button_recom)

@bot.callback_query_handler(func=lambda call: call.data == 'delete_help')
def del_help(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'delete_recom')
def del_recom(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)






@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
                 "\U0001F44B Привет! Я - бот, который может проговорить любой текст любым голосом.\nПросто отправь мне голосовое сообщение с голосом, которым ты хочешь озвучить текст.")


@bot.message_handler(commands=['recom'])
def send_recom(message):
    bot.send_message(message.chat.id,
                 "Длительность голосового сообщения желательно 7-9 секунд. Убедитесь что в сообщении нет фоновых шумов или музыки, например, во многих фильмах есть тихая музыка, когда многие актеры разговаривают.\nЖелательно чтобы не было никаких больших пауз, пробелов или других звуков.\nУбедитесь, что сообщение не начинается и не заканчивается дышащими звуками (вдох/выдох и т.д.)", reply_markup=keyboard2)



@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id,
                 "1. Отправьте голосовое сообщение в качестве примера для генерации\n(желательно посмотреть рекомендации по записи /recom)\n2. Напишите текст для генерации голосового сообщения. (Не больше 175 символов)\n3. Ожидайте отправки результата", reply_markup=keyboard1)

@bot.message_handler(func=lambda message: message.text == '\U0001F50AСгенерировать голосовое сообщение')
def handle_help_message(message):
    markup = telebot.types.ReplyKeyboardRemove(selective=False)
    bot.send_message(message.chat.id, 'Отправь голосовое сообщение в качестве примера.\n'
                          'Рекомендации по записи: /recom', reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    bot.reply_to(message, 'Чтобы начать, отправь голосовое сообщение в качестве примера\nИнструкция по использованию: /help')


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
    button_help = telebot.types.KeyboardButton(text="\U0001F50AСгенерировать голосовое сообщение")
    keyboard.add(button_help)
    text = message.text
    if len(message.text) > 175:
        bot.send_message(message.chat.id, "Ошибка. Текст не должен превышать 175 символов.")
    else:
        mesg = bot.send_message(message.chat.id, '\U000023F3 Добавил в очередь на генерацию.')
        msg = bot.send_sticker(message.chat.id,
                               'CAACAgIAAxkBAAEFnUJmTkkRPRu3jBOeQxpS-No2ccABKgACQwEAAs0bMAiAvonYgQO9kzUE')


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
            subprocess.run(['ffmpeg', '-i', f'output_audio_{filename}.wav', '-c:a', 'libopus', f'output_audio_{filename}.ogg'])
            output_audio_file_name = f'output_audio_{filename}.ogg'
            voice = open(output_audio_file_name, 'rb')
            bot.send_voice(message.chat.id, voice)
            bot.send_message(message.chat.id,
                             f'Результат генерации по запросу "*{text}*"', reply_markup=keyboard, parse_mode="Markdown")
            bot.send_message(message.chat.id, '')
            file.close()
            bot.delete_message(message.chat.id, msg.id)
            bot.delete_message(message.chat.id, mesg.id)
            os.remove(f'/root/speakers/{filename}.wav')
            os.remove(f'/root/xt/output_audio_{filename}.wav')
            os.remove(f'/root/xt/output_audio_{filename}.ogg')

        else:

            bot.send_message(message.chat.id, 'Ошибка. Попробуйте еще раз или позже.\nРекомендации для записи голосового сообщения - /recom\nИнструкция по использованию - /help')
            bot.send_message(admin_id, f'Error in api: {traceback.format_exc()}')





bot.polling()
