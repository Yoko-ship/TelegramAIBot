import telebot;
import google.generativeai as genai
import os
from PIL import Image
import requests
from io import BytesIO
from pptx import Presentation
import mimetypes


apiKey = os.getenv("TELEGRAM_TOKEN")
genai.configure(api_key=apiKey)
model = genai.GenerativeModel("gemini-1.5-flash")

def presentationToText(pathFile,message):
    try:

        prs = Presentation(pathFile)
        text = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape,"text"):
                    text.append(shape.text)
        return "\n".join(text)
    except Exception:
        bot.send_message(message.from_user.id,"Пожалуйста, отправьте презентацию повторно.")



bot = telebot.TeleBot("7429366923:AAHGpTLn2wjz7S1jr01ttdj-_Vmz00ma3l8")

@bot.message_handler(content_types=["text","document"])
def get_text_messages(message):
    if message.text == "Привет":
        bot.send_message(message.from_user.id,"Привет чем могу помочь")
    elif message.text == "Как дела" or message.text == "Как дела?":
        bot.send_message(message.from_user.id,"У меня все отлично,как у тебя?")

    elif message.text == "/help":
        bot.send_message(message.from_user.id,"Доступные команды: /help  /info /image /pdf  /present")

    elif message.text == "/image":
            bot.send_message(message.from_user.id,"В этой функции бот получает ссылку на изображение, загружает его и превращает визуальный образ в изящное текстовое описание, создавая словесную картину, понятную пользователю.")
            
            bot.reply_to(message,"Отправьте ссылку на изображение")
            bot.register_next_step_handler(message,get_url)




    elif message.text == "/info":
        bot.send_message(message.from_user.id,"Йоу-йоу, я тут, чтобы помочь, побазарить или просто быть твоим цифровым бро! 🫡 Не стесняйся спросить хоть что — инфа, советы, или даже если надо просто поплакаться в виртуальное плечо 😎. Я всегда на связи, без перерывов на кофе и драм! Давай дружить — обещаю не писать «кек» слишком часто... ну, может, чуть-чуть 👀.")
    
    elif message.text == "/present":
        bot.send_message(message.from_user.id,"Отправьте презентацию")
        bot.register_next_step_handler(message,present_handler)

    elif message.text == "/pdf":
        bot.send_message(message.from_user.id,"Отправьте пдф файл")
        bot.register_next_step_handler(message,pdf_handler)


    else:
        
        try:
            response = model.generate_content(message.text)
            responseText = response.text
            replacedText = responseText.replace("*","")
            bot.send_message(message.from_user.id,replacedText)
        except Exception as e:
            bot.send_message(message.from_user.id,f"Пришлите текст:{e}")

    

def get_url(message):
    url = message.text
    if message.text == "/stop":
        bot.reply_to(message,"Вы приостановили функцию")
        bot.register_next_step_handler(message,get_text_messages)
    else:
        try:
            responseUrl = requests.get(url)
            pictureDescribe = Image.open(BytesIO(responseUrl.content))
            responseChat = model.generate_content(["Опиши эту картинку на русском",pictureDescribe])
            bot.send_message(message.from_user.id,responseChat.text)

        except Exception as e:
            bot.send_message(message.from_user.id,f"Не правильный url или данные,попробуйте ещё раз {e}// Напишите /stop чтобы приостановить данную функцию")
            bot.register_next_step_handler(message,get_url)



@bot.message_handler(content_types=["text","document"])
def present_handler(message):
        if message.text == "/stop":
            bot.reply_to(message,"Вы приостановили функцию")
            bot.register_next_step_handler(message,get_text_messages)
        else:
            try:
                file_info = bot.get_file(message.document.file_id)
            except Exception:
                bot.reply_to(message,"Отправленный документ не является презентацией,попробуйте ещё раз")
                bot.register_next_step_handler(message,present_handler)
                return

            try:
                dowloaded_file = bot.download_file(file_info.file_path)
            except Exception as e:
                bot.reply_to(message,e)
                return
            try:

                file_name = message.document.file_name
                with open(file_name,"wb") as new_file:
                    new_file.write(dowloaded_file)

                pdftoText = presentationToText(file_name,message.from_user.id)
                response = model.generate_content(["Опиши это кратко но подробно желательно с примерами",pdftoText])
                responseText = response.text.replace("*","")
                bot.send_message(message.from_user.id,responseText)
            except AttributeError:
                bot.send_message(message.from_user.id,"Пришлите документ в виде презентации")
                bot.register_next_step_handler(message,present_handler)

            except Exception as e:
                bot.reply_to(message,e)
            

def pdf_handler(message):
    if message.text == "/stop":
        bot.reply_to(message,"Вы приостановили функцию")
        bot.register_next_step_handler(message,get_text_messages)
    else:
        try:
            pdf_info = bot.get_file(message.document.file_id)
        except Exception as e:
            bot.reply_to(message,"Отправленный документ не является пдф файлом")
            bot.register_next_step_handler(message,pdf_handler)
            return
        try:
            dowloaded_pdf = bot.download_file(pdf_info.file_path)
            pdf_name = message.document.file_name
            with open(pdf_name,"wb") as new_pdf:
                new_pdf.write(dowloaded_pdf)

            mime_type,_ = mimetypes.guess_type(pdf_name)
            if mime_type is None:
                mime_type = "application/pdf"



            with open(pdf_name,"rb") as pdf_file:
                sample_pdf = genai.upload_file(pdf_file,mime_type=mime_type)
        except Exception as e:
            bot.reply_to(message,e)
            return
        try:

            response = model.generate_content(["Опиши это кратко но подробно желательно с примерами",sample_pdf])
            responseText = response.text.replace("*","")
            bot.send_message(message.from_user.id,responseText)
        except Exception as e:
            bot.reply_to(message,f"Произошла ошибка, не поддерживаемый формат {e}")
            bot.register_next_step_handler(message,pdf_handler)

        


bot.polling(none_stop=True,interval=0)

