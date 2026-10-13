import datetime


CATEGORY_EMOJI = {
    'Python': '🐍',
    'AI/ML': '🤖',
    'Web': '🌐',
    'ИБ': '🔐',
    'Карьера': '💼'
}


def sender(data: list)->str:
    message = f"🔥 *Дайджест Хабра* | {datetime.date.today().strftime('%d.%m.%Y')}\n"
    message += f"📊 Найдено полезных статей: *{len(data)}*\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    if len(data)>=7:
        lst_art=data[:2]
        for cat in CATEGORY_EMOJI:
            for j in data[2:]:
                if j[3]==cat:
                    lst_art.append(j)
                    break
    else:
        lst_art=data

    for art in lst_art:
        em = CATEGORY_EMOJI.get(art[3], '')
        message+=f'{em}*{art[0]}*{em}\n\n'
        message+=f'Причина: {art[1]}\n'
        message+=f'🔗[Читать на Хабре]({art[2]})\n\n'

    if len(data) >= 7:
        message+='Остальные новости загружены в бд\n'
    message += "━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "📅 Следующий выпуск: завтра в 09:15"

    return message


    