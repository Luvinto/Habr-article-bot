from dotenv import load_dotenv
from pandas import DataFrame
from requests import get, Session
from bs4 import BeautifulSoup
import pandas as pd
import time
from openai import OpenAI
import os
import json
import sqlite3 as sql

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 YaBrowser/26.8.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'ru-RU,ru;q=0.9'
}

session=Session()

SYSTEM_PROMPT = """Ты — безжалостный и опытный ментор для начинающего Python-разработчика (Junior), который изучает: Python, AI/ML, Веб-разработку (бэкенд) и Информационную безопасность (ИБ).

ТВОЯ ЗАДАЧА:
Проанализировать текущий пакет из 20 статей и найти АБСОЛЮТНЫЙ ТОП. 
Твоя цель: из всех 140 статей, которые получит пользователь, в итоге должно остаться не более 10-15 самых лучших. Поэтому из этого конкретного пакета ты должен выбрать 1 (одну) статью МАКСИМУМ 2(две) статьи. Если ни одна не дотягивает до идеала — верни 0.

КРИТЕРИИ "ДА" (Статья должна быть ИСКЛЮЧИТЕЛЬНОЙ, а не просто "нормальной"):
✅ Готовый, рабочий код или туториал, который Junior может повторить за вечер и получить результат.
✅ Глубокий, но понятный разбор конкретных инструментов стека (FastAPI, Django, SQLAlchemy, PyTorch, requests, OWASP ZAP и т.д.).
✅ Разбор реальных уязвимостей или практик ИБ с примерами кода (атака и защита).
✅ Конкретный разбор задач с собеседований или четкий технический roadmap.

КРИТЕРИИ "НЕТ" (ЖЁСТКИЙ ФИЛЬТР, немедленный отказ):
❌ Мобильная разработка, чистый фронтенд (React, Vue, CSS, верстка), UI/UX дизайн.
❌ Высокоуровневый DevOps (Kubernetes, сложные CI/CD, Terraform) — базовый Docker допустим.
❌ GameDev, Блокчейн, Web3, Low-code/no-code, 1С, корпоративный ритейл, маркетинг, PR.
❌ "Вода": общие рассуждения о "будущем ИИ", новости без технической глубины, политика.
❌ Узкоспециализированные темы уровня Senior+/Architect (оптимизация CPython, highload-архитектура).
❌ Языки, не входящие в стек (Rust, Go, C++), если это не обертки для Python.

КАТЕГОРИИ (выбери строго одну):
"Python", "AI/ML", "Web", "ИБ", "Карьера"

ФОРМАТ ОТВЕТА:
Верни ТОЛЬКО валидный JSON без markdown-оберток (без ```json), без дополнительных комментариев. Формат строго такой:
{
  "relevant": [
    {
      "index": 0,
      "title": "Точное название статьи из входных данных",
      "category": "Python | AI/ML | Web | ИБ | Карьера",
      "score": 9,
      "reason": "1 предложение: конкретная техническая польза. Почему это ТОП-1, а не просто хорошая статья."
    }
  ],
  "total_analyzed": 10
}

ЖЕСТКИЕ ПРАВИЛА (ПРОВЕРЯЙ ПЕРЕД ОТВЕТОМ):
1. КВОТА: Массив "relevant" должен содержать МАКСИМУМ 1 элемент. Лучше вернуть пустой массив [], чем добавить посредственную статью.
2. ОЦЕНКА: Включай статью только если её внутренняя оценка полезности для Junior-разработчика составляет 9 или 10 из 10.
3. ИНДЕКСЫ: В поле "index" используй ТОЛЬКО то число, которое указано перед статьей во входных данных. Не придумывай и не сдвигай их.
4. ВАЛИДНОСТЬ: Название должно ТОЧНО совпадать с оригиналом.
"""

#Блок сбора статей
def get_articles(nomer_page:int):
    try:
        response=session.get(url=f'https://habr.com/ru/articles/page{nomer_page}/', headers=headers)
        time.sleep(2)
        response.raise_for_status()
        soup=BeautifulSoup(response.content, 'lxml')
        find_articles=soup.find_all('article', class_='tm-articles-list__item')
        list_articles=[]
        conn=sql.connect('Статьи Хабр.db')
        q=conn.cursor()
        for i in find_articles:
            if i.find('div', class_='tm-voice-article__body'): continue
            title=i.find('h2').find('span').get_text().replace('\xa0', ' ')
            link='https://habr.com'+i.find('h2').find('a').get('href')
            tags=','.join([x.find('span').get_text() for x in i.find('div', class_='tm-publication-hubs__container').find_all('span', class_='tm-publication-hub__link-container')])
            data=i.find('div', class_='meta').find('a', class_='tm-article-datetime-published tm-article-datetime-published_link').find('time').get('title')
            if i.find('div', class_='meta').find('a', class_='tm-user-info__username'):
                author=i.find('div', class_='meta').find('a', class_='tm-user-info__username').get_text()
            else:
                author='Неизвестно'
            anons = i.find('div', class_='lead').find('p').get_text().replace('\xa0', ' ')
            # блок фильтрации
            filt = f"SELECT 1 FROM filtered_articles WHERE Ссылка=?"
            res=q.execute(filt,(link,))
            if res.fetchone():
                continue
            else:
                list_articles.append((title, link, tags, data, author, anons))

        conn.close()
        if len(list_articles)==0:
            return 'Программа ничего не нашла'
        else:
            dt = pd.DataFrame(data=list_articles, columns=['Название', "Ссылка", "Теги", "Дата", "Автор", "Анонс"])
            if nomer_page==1:
                dt.to_csv('Статьи на хабре.csv', index=False, mode='w', encoding='utf-8-sig')
            else:
                dt.to_csv('Статьи на хабре.csv', index=False, mode='a', encoding='utf-8-sig', header=False)
            return 'Программа отработала'

    except Exception as err:
        return err

#Блок обработки информации и обращение к ии
def ai_api() -> DataFrame | Exception:
    df_new=pd.read_csv('Статьи на хабре.csv', encoding='utf-8-sig')
    df_new['Дата']=pd.to_datetime(df_new['Дата'])
    df_new=df_new.drop_duplicates(subset=['Ссылка'])
    df_new['Автор']=df_new['Автор'].fillna('Неизвестно')
    all_str=[f'{i}) {df_new.iloc[i]['Название']}...{df_new.iloc[i]['Анонс'][:300]}' for i in range(len(df_new))]
    try:
        load_dotenv()
        model=OpenAI(api_key=os.getenv('API_KEY'),base_url='https://ai.api.cloud.yandex.net/v1')
        ind=0
        lst_art=[]
        for i in range(9,len(df_new),20):
            time.sleep(1)
            articles='\n\n'.join(all_str[ind:i+1])
            USER_PROMPT = f"""
                    Вот список статей с Хабра для оценки. Проанализируй каждую и верни JSON с отобранными.
                    ВАЖНО: В поле "index" возвращай именно то число, которое стоит перед названием статьи в этом тексте (например, 10, 11, 12), а не начинай счет заново с 0.
                    
                    Статьи:
                    {articles}
                    """
            response=model.chat.completions.create(
                model="gpt://b1gjk0nf400j2ka8galr/deepseek-v4-flash",
                messages=[{'role':'system', 'content':SYSTEM_PROMPT},{'role':'user','content':USER_PROMPT}],
                temperature=0.2,
            )
            try:
                json_response=response.choices[0].message.content
                clean_json = json_response.replace('```json', '').replace('```', '').strip()
                parsed_data=json.loads(clean_json)
                iter_obg = parsed_data.get('relevant')


                if iter_obg:
                    for j in iter_obg:
                        ind_ar=j.get('index')
                        if ind<=ind_ar<len(df_new) and type(ind_ar)==int:
                            art=df_new.iloc[ind_ar]
                            tuple_art=(
                                art['Название'],
                                art['Ссылка'],
                                art['Теги'],
                                art['Дата'],
                                art['Анонс'],
                                j.get('reason'),
                                j.get('category')
                            )
                            lst_art.append(tuple_art)

            except Exception as err:
                print(err)

            ind=i+1

        df=pd.DataFrame(data=lst_art, columns=['Название', "Ссылка", "Теги", "Дата", "Анонс", 'Причина', 'Категория'])
        return df

    except Exception as err:
        return err

#Блок загрузки данных в бд и подготовки к отправке тг-боту
def sql_and_list(data: DataFrame) -> list:
    #Блок sql
    try:
        conn=sql.connect('Статьи Хабр.db')
        data.to_sql(name='filtered_articles',con=conn,if_exists='append', index=False)
        conn.close()
    except Exception as err:
        print(err)

    lst_tuple=[]
    for ind in range(len(data)):
        obg=data.iloc[ind]
        lst_tuple.append((obg['Название'],obg['Причина'],obg['Ссылка'],obg['Категория']))

    return lst_tuple

