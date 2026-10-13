from dotenv import load_dotenv
from requests import post
from sen import sender
from parser_api_sql import get_articles, ai_api, sql_and_list
import os
from pandas import DataFrame


load_dotenv()

headers = {
    "Title": f"Habr Digest",
    "Tags": "rocket,book",  # Эмодзи для уведомления
    "Markdown": "yes"       # Включаем поддержку жирного шрифта
}

try:
    for i in range(1,8):
        result1=get_articles(nomer_page=i)
        print(result1)

    print('Данные спаршены')
    data=ai_api()
    if type(data)==DataFrame:
        print('Данные от ИИ получены')
        result2=sql_and_list(data)
        message=sender(result2)
        response=post(url=os.getenv('URL'), data=message.encode('utf8'), headers=headers)
        print(response)


except Exception as err:
    print(err)
