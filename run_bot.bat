@echo off
echo [%date% %time%] === Запуск === >> last_run.log

REM Переходим в папку проекта
cd /d "C:\Users\Honor\PycharmProjects\requests\tb-habr"

REM Активируем виртуальное окружение (используем абсолютный путь для надежности)
call "C:\Users\Honor\PycharmProjects\requests\.venv\Scripts\activate.bat"

REM Запускаем скрипт с отключенной буферизацией (-u)
python -u main.py >> last_run.log 2>&1

echo [%date% %time%] === Завершено === >> last_run.log

REM ВАЖНО: Убираем pause, добавляем явный exit
exit /b 0