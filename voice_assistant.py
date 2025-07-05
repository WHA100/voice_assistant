import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import webbrowser
import datetime
import traceback
import random
import ctypes
import subprocess
import time
import pyautogui
import requests
import tempfile
import wave
import pyaudio
import asyncio
import edge_tts
import pygame
import pyttsx3
import win32api
import winshell

# --- Путь к модели Vosk (скачайте и распакуйте модель в папку 'vosk-model-small-ru') ---
VOSK_MODEL_PATH = 'vosk-model-small-ru'

# --- Настройки Ollama ---
OLLAMA_MODEL = 'gemma3'
OLLAMA_URL = 'http://localhost:11434/api/generate'

# --- Инициализация TTS ---
def init_tts():
    """Инициализация текстово-речевого синтезатора с улучшенными настройками"""
    try:
        engine = pyttsx3.init()
        
        # Получаем список доступных голосов
        voices = engine.getProperty('voices')
        
        # Ищем лучший русский голос
        best_voice = None
        for voice in voices:
            voice_name = voice.name.lower()
            voice_id = voice.id.lower()
            
            # Приоритет: русские голоса
            if 'russian' in voice_name or 'ru' in voice_id or 'русский' in voice_name:
                best_voice = voice.id
                break
            # Запасной вариант: английские голоса
            elif 'english' in voice_name or 'en' in voice_id:
                if not best_voice:
                    best_voice = voice.id
        
        # Устанавливаем голос
        if best_voice:
            engine.setProperty('voice', best_voice)
        
        # Оптимальные настройки для красивого голоса
        engine.setProperty('rate', 140)      # Скорость речи (было 150)
        engine.setProperty('volume', 0.9)    # Громкость (было 0.8)
        
        # Дополнительные настройки для Windows
        try:
            # Настройка качества голоса (если поддерживается)
            engine.setProperty('quality', 'high')
        except:
            pass
        
        return engine
    except Exception as e:
        print(f"Ошибка инициализации TTS: {e}")
        return None

# --- Функция для работы с Ollama ---
def ask_ollama(question, max_tokens=500):
    """Отправка запроса к Ollama и получение ответа"""
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": f"Отвечай на русском языке кратко и по делу. Вопрос: {question}",
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'Извините, не удалось получить ответ.')
        else:
            return f"Ошибка API: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Ошибка соединения с Ollama: {str(e)}"
    except Exception as e:
        return f"Неожиданная ошибка: {str(e)}"

# --- Функция озвучивания текста через edge-tts ---
def speak_text(text):
    """Озвучивание текста через Microsoft Edge TTS (Svetlana Neural)"""
    def run_tts():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_speak_text_edge_tts(text))
        except Exception as e:
            print(f"Ошибка edge-tts: {e}")
    threading.Thread(target=run_tts, daemon=True).start()

async def _speak_text_edge_tts(text):
    try:
        temp_filename = tempfile.mktemp(suffix='.mp3')
        communicate = edge_tts.Communicate(text, "ru-RU-SvetlanaNeural")
        await communicate.save(temp_filename)
        pygame.mixer.init()
        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
        try:
            os.unlink(temp_filename)
        except:
            pass
    except Exception as e:
        print(f"Ошибка edge-tts: {e}")

# --- Проверка доступности Ollama ---
def check_ollama_availability():
    """Проверка доступности Ollama сервиса"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        return response.status_code == 200
    except:
        return False

# --- Звуковые эффекты для команд ---
COMMAND_SOUNDS = {
    'привет': ['beep_high', 'beep_medium'],
    'браузер': ['beep_medium'],
    'ютуб': ['beep_medium'],
    'блокнот': ['beep_medium'],
    'калькулятор': ['beep_medium'],
    'проводник': ['beep_medium'],
    'выключи компьютер': ['beep_low'],
    'заблокируй экран': ['beep_low'],
    'панель управления': ['beep_medium'],
    'время': ['beep_high'],
    'пока': ['beep_low', 'beep_medium'],
    'default': [
        'beep_medium',
        'beep_high',
        'beep_low',
        'beep_medium',
        'beep_high',
        'beep_medium',
    ],
    'скриншот': ['beep_high'],
    'звук выкл': ['beep_medium'],
    'звук вкл': ['beep_medium'],
    'громче': ['beep_medium'],
    'тише': ['beep_medium'],
    'звук 20': ['beep_medium'],
    'звук 50': ['beep_medium'],
    'звук 80': ['beep_medium'],
    'звук 100': ['beep_medium'],
    'язык': ['beep_medium'],
    'язык русский': ['beep_medium'],
    'язык английский': ['beep_medium'],
    'свернуть окна': ['beep_medium'],
    'корзина': ['beep_medium'],
    'буфер обмена': ['beep_medium'],
}

# --- Синонимы команд (ключ — синоним, значение — главная команда) ---
COMMAND_SYNONYMS = {
    # browser
    'открой браузер': 'браузер',
    'запусти браузер': 'браузер',
    'закрой браузер': 'браузер',
    'выключи браузер': 'браузер',
    # youtube
    'открой ютуб': 'ютуб',
    'запусти ютуб': 'ютуб',
    # calculator
    'включи калькулятор': 'калькулятор',
    'открой калькулятор': 'калькулятор',
    'покажи калькулятор': 'калькулятор',
    'запусти калькулятор': 'калькулятор',
    'калькулятор': 'калькулятор',
    'закрой калькулятор': 'калькулятор',
    'отключи калькулятор': 'калькулятор',
    'выключи калькулятор': 'калькулятор',
    'убери калькулятор': 'калькулятор',
    # notepad
    'открой блокнот': 'блокнот',
    'запусти блокнот': 'блокнот',
    # explorer
    'открой проводник': 'проводник',
    'запусти проводник': 'проводник',
    # power
    'выключи компьютер': 'выключи компьютер',
    'заверши работу': 'выключи компьютер',
    'выруби комп': 'выключи компьютер',
    'выключи комп': 'выключи компьютер',
    # lock
    'заблокируй экран': 'заблокируй экран',
    'заблокируй компьютер': 'заблокируй экран',
    'заблокируй комп': 'заблокируй экран',
    # control panel
    'открой панель управления': 'панель управления',
    'запусти панель управления': 'панель управления',
    # time
    'сколько времени': 'время',
    'который час': 'время',
    # bye
    'до свидания': 'пока',
    'выключись': 'пока',
    'выруби себя': 'пока',
    # приветствие
    'доброе утро': 'привет',
    'привет': 'привет',
    # humor
    'расскажи анекдот': 'шутка',
    'рассмеши': 'шутка',
    'пошути': 'шутка',
    'шутка': 'шутка',
    'расскажи шутку': 'шутка',
    'развесели меня': 'шутка',
    'что-нибудь смешное': 'шутка',
    'подними мне настроение': 'шутка',
    'мне скучно': 'шутка',
    'хочу шутку': 'шутка',
    'хочу анекдот': 'шутка',
    'расскажи что-нибудь смешное': 'шутка',
    'расскажи смешное что-нибудь': 'шутка',
    'хочу посмеяться': 'шутка',
    # thanks
    'спасибо': 'благодарность',
    'молодец': 'благодарность',
    'респект': 'благодарность',
    'ты супер': 'благодарность',
    'отличная работа': 'благодарность',
    'ты крут': 'благодарность',
    'ты большой молодец': 'благодарность',
    'ты реально крут': 'благодарность',
    'ты офигенный': 'благодарность',
    # terminate
    'выключись': 'пока',
    'вырубись': 'пока',
    'завершить работу': 'пока',
    'закройся': 'пока',
    'отключись': 'пока',
    'завершить свою работу': 'пока',
    'на сегодня хватит': 'пока',
    'выгрузи себя из памяти': 'пока',
    'ты мне надоел': 'пока',
    'пора спать': 'пока',
    # stupid
    'ты дурак': 'оскорбление',
    'ты дебил': 'оскорбление',
    'ты глупый': 'оскорбление',
    'ты тупой': 'оскорбление',
    # music
    'открой музыку': 'музыка',
    'запусти музыку': 'музыка',
    'включи музыку': 'музыка',
    'выключи музыку': 'музыка',
    'отключи музыку': 'музыка',
    'закрой музыку': 'музыка',
    # steam
    'открой стим': 'стим',
    'запусти стим': 'стим',
    'включи стим': 'стим',
    'выключи стим': 'стим',
    'отключи стим': 'стим',
    'закрой стим': 'стим',
    # диспетчер задач
    'открой диспетчер задач': 'диспетчер задач',
    'запусти диспетчер задач': 'диспетчер задач',
    'диспетчер задач': 'диспетчер задач',
    # буфер обмена
    'открой буфер обмена': 'буфер обмена',
    'покажи буфер обмена': 'буфер обмена',
    'запусти буфер обмена': 'буфер обмена',
    'буфер обмена': 'буфер обмена',
    # корзина
    'очисти корзину': 'корзина',
    'почисти корзину': 'корзина',
    'очистка корзины': 'корзина',
    # громкость
    'выключи звук': 'звук выкл',
    'беззвучный режим': 'звук выкл',
    'отключи звук': 'звук выкл',
    'включи звук': 'звук вкл',
    'режим со звуком': 'звук вкл',
    'верни звук': 'звук вкл',
    'сделай громче': 'громче',
    'громче': 'громче',
    'сделай погромче': 'громче',
    'сделай тише': 'тише',
    'тише': 'тише',
    'сделай потише': 'тише',
    # язык
    'смени раскладку': 'язык',
    'поменяй раскладку': 'язык',
    'смени язык': 'язык',
    'поменяй язык': 'язык',
    'переключи на русский': 'язык русский',
    'переключи на английский': 'язык английский',
    'смени раскладку на русскую': 'язык русский',
    'поменяй раскладку на русскую': 'язык русский',
    'поменяй раскладку на английскую': 'язык английский',
    'смени раскладку на английскую': 'язык английский',
    'смени язык на русский': 'язык русский',
    'поменяй язык на русский': 'язык русский',
    'смени язык на английский': 'язык английский',
    'поменяй язык на английский': 'язык английский',
    # папки
    'открой загрузки': 'загрузки',
    'открой документы': 'документы',
    'открой рабочий стол': 'рабочий стол',
    # поиск
    'найди в интернете': 'поиск',
    'поиск': 'поиск',
    # погода
    'погода': 'погода',
    'какая погода': 'погода',
    # системная информация
    'системная информация': 'системная информация',
    'информация о системе': 'системная информация',
    # свернуть окна
    'сверни все окна': 'свернуть окна',
    'сверни окна': 'свернуть окна',
    # игровой режим и рабочий режим
    'включи игровой режим': 'игровой режим',
    'перейди в игровой режим': 'игровой режим',
    'я хочу поиграть': 'игровой режим',
    'запусти игровой режим': 'игровой режим',
    'давай поиграем': 'игровой режим',
    'игровой режим': 'игровой режим',
    'войди в игровой режим': 'игровой режим',
    'рабочий режим': 'рабочий режим',
    'вернись в рабочий режим': 'рабочий режим',
    'отключи игровой режим': 'рабочий режим',
    'выйди из игрового режима': 'рабочий режим',
    'выход с игрового режима': 'рабочий режим',
    'рабочее пространство': 'рабочий режим',
    'звук двадцать': 'звук 20',
    'громкость двадцать': 'звук 20',
    'поставь звук на двадцать': 'звук 20',
    'поставь громкость на двадцать': 'звук 20',
    'установи звук на двадцать': 'звук 20',
    'установи громкость на двадцать': 'звук 20',
    'звук пятьдесят': 'звук 50',
    'громкость пятьдесят': 'звук 50',
    'поставь звук на пятьдесят': 'звук 50',
    'поставь громкость на пятьдесят': 'звук 50',
    'установи звук на пятьдесят': 'звук 50',
    'установи громкость на пятьдесят': 'звук 50',
    'звук восемьдесят': 'звук 80',
    'громкость восемьдесят': 'звук 80',
    'поставь звук на восемьдесят': 'звук 80',
    'поставь громкость на восемьдесят': 'звук 80',
    'установи звук на восемьдесят': 'звук 80',
    'установи громкость на восемьдесят': 'звук 80',
    'звук сто': 'звук 100',
    'громкость сто': 'звук 100',
    'поставь звук на сто': 'звук 100',
    'поставь громкость на сто': 'звук 100',
    'установи звук на сто': 'звук 100',
    'установи громкость на сто': 'звук 100',
}

# --- Функции для команд ---
def open_browser():
    webbrowser.open('https://ya.ru/')

def open_youtube():
    webbrowser.open('https://www.youtube.com')

def open_notepad():
    os.system('notepad')

def open_calculator():
    os.system('start calc')

def open_explorer():
    os.system('explorer')

def shutdown_computer():
    os.system('shutdown /s /t 5')

def lock_screen():
    os.system('rundll32.exe user32.dll,LockWorkStation')

def open_control_panel():
    os.system('control')

def open_task_manager():
    os.system('taskmgr')

def open_downloads():
    os.system('explorer shell:Downloads')

def open_documents():
    os.system('explorer shell:Personal')

def open_desktop():
    os.system('explorer shell:Desktop')

def open_search():
    webbrowser.open('https://ya.ru/')

def open_steam():
    try:
        os.startfile(r'C:\Program Files (x86)\Steam\steam.exe')
    except:
        try:
            os.startfile(r'C:\Program Files\Steam\steam.exe')
        except:
            webbrowser.open('https://store.steampowered.com')

def close_steam():
    os.system('taskkill /IM steam.exe /F')

def open_telegram():
    try:
        # Попробуем несколько возможных путей
        telegram_paths = [
            r'C:\Users\user\AppData\Roaming\Telegram Desktop\Telegram.exe',
            r'C:\Users\%USERNAME%\AppData\Roaming\Telegram Desktop\Telegram.exe',
            r'C:\Program Files\Telegram Desktop\Telegram.exe',
            r'C:\Program Files (x86)\Telegram Desktop\Telegram.exe'
        ]
        
        for path in telegram_paths:
            if os.path.exists(path):
                os.startfile(path)
                return
        
        # Если не найден, открываем веб-версию
        webbrowser.open('https://web.telegram.org')
    except:
        webbrowser.open('https://web.telegram.org')

def get_system_info():
    import platform
    info = f"ОС: {platform.system()} {platform.release()}\n"
    info += f"Версия: {platform.version()}\n"
    info += f"Архитектура: {platform.machine()}\n"
    info += f"Процессор: {platform.processor()}"
    
    # Сохраняем в файл и открываем
    with open('system_info.txt', 'w', encoding='utf-8') as f:
        f.write(info)
    os.system('notepad system_info.txt')

def get_weather():
    webbrowser.open('https://www.google.com/search?q=погода')

def play_music():
    webbrowser.open('https://www.youtube.com/music')

# --- Дополнительные функции для команд ---
def mute_volume():
    pyautogui.press('volumemute')

def unmute_volume():
    pyautogui.press('volumemute')  # Обычно это же действие

def volume_up():
    pyautogui.press('volumeup')

def volume_down():
    pyautogui.press('volumedown')

def minimize_all_windows():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)  # SW_MINIMIZE
    ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win
    ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)  # D
    ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)
    ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)

def take_screenshot():
    pyautogui.press('printscreen')
    time.sleep(0.5)

def switch_language(lang=None):
    import win32api
    if lang == 'ru':
        win32api.LoadKeyboardLayout('00000419', 1)
    elif lang == 'en':
        win32api.LoadKeyboardLayout('00000409', 1)
    else:
        pyautogui.hotkey('altleft', 'shiftleft')

def open_clipboard():
    os.system('explorer.exe shell:::{1C3B4210-F441-11CE-B9EA-00AA006B1A69}')

def empty_recycle_bin():
    import winshell
    winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=True)

def set_volume(level):
    # Сбросить на минимум, затем поднять до нужного уровня
    for _ in range(50):
        pyautogui.press('volumedown')
    steps = int(level / 10)  # Теперь 10% за шаг
    for _ in range(steps):
        pyautogui.press('volumeup')

# --- Обновленный словарь команд ---
COMMANDS = {
    'привет': ('Выполняю.', None),
    'браузер': ('Выполняю.', open_browser),
    'ютуб': ('Выполняю.', open_youtube),
    'блокнот': ('Выполняю.', open_notepad),
    'калькулятор': ('Выполняю.', open_calculator),
    'проводник': ('Выполняю.', open_explorer),
    'выключи компьютер': ('Выполняю.', shutdown_computer),
    'заблокируй экран': ('Выполняю.', lock_screen),
    'панель управления': ('Выполняю.', open_control_panel),
    'время': ('Выполняю.', None),
    'пока': ('Выполняю.', None),
    'шутка': ('Выполняю.', None),
    'благодарность': ('Выполняю.', None),
    'оскорбление': ('Выполняю.', None),
    'музыка': ('Выполняю.', play_music),
    'стим': ('Выполняю.', open_steam),
    'диспетчер задач': ('Выполняю.', open_task_manager),
    'буфер обмена': ('Выполняю.', open_clipboard),
    'корзина': ('Выполняю.', empty_recycle_bin),
    'скриншот': ('Выполняю.', take_screenshot),
    'звук выкл': ('Выполняю.', mute_volume),
    'звук вкл': ('Выполняю.', unmute_volume),
    'громче': ('Выполняю.', volume_up),
    'тише': ('Выполняю.', volume_down),
    'язык': ('Выполняю.', switch_language),
    'язык русский': ('Выполняю.', lambda: switch_language('ru')),
    'язык английский': ('Выполняю.', lambda: switch_language('en')),
    'загрузки': ('Выполняю.', open_downloads),
    'документы': ('Выполняю.', open_documents),
    'рабочий стол': ('Выполняю.', open_desktop),
    'поиск': ('Выполняю.', open_search),
    'погода': ('Выполняю.', get_weather),
    'системная информация': ('Выполняю.', get_system_info),
    'свернуть окна': ('Выполняю.', minimize_all_windows),
    'игровой режим': ('Выполняю.', open_steam),
    'рабочий режим': ('Выполняю.', close_steam),
    'звук 20': ('Выполняю.', lambda: set_volume(20)),
    'звук 50': ('Выполняю.', lambda: set_volume(50)),
    'звук 80': ('Выполняю.', lambda: set_volume(80)),
    'звук 100': ('Выполняю.', lambda: set_volume(100)),
    'телеграм': ('Выполняю.', open_telegram),
}

# --- Фразы подтверждения команд ---
COMMAND_CONFIRMATIONS = {k: 'Выполняю.' for k in COMMANDS.keys()}

# --- Шутки и благодарности ---
JOKES = [
    'Почему программисты путают Хэллоуин и Рождество? Потому что 31 OCT = 25 DEC!',
    'Зачем программисту очки? Чтобы видеть C#!',
    'Баг — это не ошибка, это неожиданная фича!',
]
THANKS_RESPONSES = [
    'Спасибо! Я стараюсь!',
    'Всегда рад помочь!',
    'Обращайтесь, сэр!',
]
INSULT_RESPONSES = [
    'Сам такой!',
    'Обидно, но я не обижаюсь.',
    'Я просто искусственный интеллект, не обижайте меня!',
]

# --- Логирование ошибок ---
def log_error(e):
    with open('error_log.txt', 'a', encoding='utf-8') as f:
        f.write(traceback.format_exc() + '\n')

# --- Класс голосового ассистента ---
class VoiceAssistant:
    def __init__(self, model_path, device):
        self.model = Model(model_path)
        self.device = device
        device_info = sd.query_devices(device, 'input')
        self.samplerate = int(device_info.get('default_samplerate', 16000))
        self.q = queue.Queue()
        self.rec = KaldiRecognizer(self.model, self.samplerate)
        self.running = False

    def callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.q.put(bytes(indata))

    def listen(self, on_result, on_error):
        def _listen():
            try:
                with sd.RawInputStream(samplerate=self.samplerate, blocksize = 8000, device=self.device, dtype='int16', channels=1, callback=self.callback):
                    while self.running:
                        data = self.q.get()
                        if self.rec.AcceptWaveform(data):
                            result = json.loads(self.rec.Result())
                            text = result.get('text', '').strip()
                            if text:
                                on_result(text)
            except Exception as e:
                log_error(e)
                on_error(e)
        self.running = True
        threading.Thread(target=_listen, daemon=True).start()

    def stop(self):
        self.running = False

# --- GUI ---
class AssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Голосовой помощник с AI (Vosk + Ollama)')
        self.root.geometry('700x600')
        self.root.resizable(False, False)
        self.assistant = None
        self.is_listening = False
        self.is_processing_ai = False  # Флаг обработки AI запроса
        self.ollama_available = check_ollama_availability()

        # Статус ассистента
        self.status_label = tk.Label(root, text='Ассистент выключен', fg='red', font=('Arial', 12, 'bold'))
        self.status_label.pack(pady=(10, 0))

        # Статус AI
        ai_status = "AI доступен" if self.ollama_available else "AI недоступен"
        ai_color = 'green' if self.ollama_available else 'red'
        self.ai_status_label = tk.Label(root, text=f'AI статус: {ai_status}', fg=ai_color, font=('Arial', 10))
        self.ai_status_label.pack(pady=(5, 0))

        # Выбор микрофона
        self.mic_label = tk.Label(root, text='Выберите микрофон:', font=('Arial', 10))
        self.mic_label.pack(pady=(10, 0))
        self.mic_combo = ttk.Combobox(root, state='readonly', width=60)
        self.mic_combo.pack(pady=5)
        self.refresh_mics()

        # Кнопка запуска
        self.start_button = tk.Button(root, text='Включить ассистента', command=self.toggle_assistant, font=('Arial', 14), width=25, bg='#4CAF50', fg='white')
        self.start_button.pack(pady=10)

        # Кнопка проверки AI
        self.check_ai_button = tk.Button(root, text='Проверить AI', command=self.check_ai, font=('Arial', 10), width=15, bg='#2196F3', fg='white')
        self.check_ai_button.pack(pady=5)

        # Лог
        self.log_text = ScrolledText(root, width=80, height=20, state='disabled', font=('Consolas', 11))
        self.log_text.pack(padx=10, pady=10)

        self.log('Добро пожаловать! Выберите микрофон, затем нажмите "Включить ассистента".')
        if self.ollama_available:
            self.log('AI (Ollama + Gemma3) доступен для ответов на общие вопросы.')
        else:
            self.log('AI недоступен. Убедитесь, что Ollama запущен.')

    def refresh_mics(self):
        devices = sd.query_devices()
        input_devices = []
        for i, device in enumerate(devices):
            try:
                if device['max_input_channels'] > 0:
                    input_devices.append(f"{i}: {device['name']}")
            except (KeyError, TypeError):
                continue
        self.mic_combo['values'] = input_devices
        if input_devices:
            self.mic_combo.current(0)

    def check_ai(self):
        """Проверка доступности AI"""
        self.ollama_available = check_ollama_availability()
        ai_status = "AI доступен" if self.ollama_available else "AI недоступен"
        ai_color = 'green' if self.ollama_available else 'red'
        self.ai_status_label.config(text=f'AI статус: {ai_status}', fg=ai_color)
        
        if self.ollama_available:
            self.log('AI (Ollama + Gemma3) доступен.')
        else:
            self.log('AI недоступен. Убедитесь, что Ollama запущен.')

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def toggle_assistant(self):
        if not self.is_listening:
            if not self.mic_combo.get():
                messagebox.showerror('Ошибка', 'Не выбран микрофон!')
                return
            device_index = int(self.mic_combo.get().split(':')[0])
            if not os.path.exists(VOSK_MODEL_PATH):
                messagebox.showerror('Ошибка', f'Папка модели Vosk не найдена: {VOSK_MODEL_PATH}\nСкачайте и распакуйте модель!')
                return
            self.assistant = VoiceAssistant(VOSK_MODEL_PATH, device_index)
            self.is_listening = True
            self.status_label.config(text='Ассистент работает', fg='green')
            self.start_button.config(text='Выключить ассистента', bg='#F44336')
            self.log('Ассистент запущен. Говорите команду...')
            self.assistant.listen(self.on_result, self.on_error)
        else:
            self.is_listening = False
            if self.assistant:
                self.assistant.stop()
            self.status_label.config(text='Ассистент выключен', fg='red')
            self.start_button.config(text='Включить ассистента', bg='#4CAF50')
            self.log('Ассистент остановлен.')

    def play_command_voice(self, cmd):
        """Воспроизведение звукового сигнала для команды"""
        sounds = COMMAND_SOUNDS.get(cmd, COMMAND_SOUNDS['default'])
        sound_type = random.choice(sounds)
        
        try:
            # Генерируем простой звуковой сигнал
            self.play_beep(sound_type)
        except Exception as e:
            print(f"Ошибка воспроизведения звука: {e}")
    
    def play_beep(self, sound_type):
        """Воспроизведение звукового сигнала определенного типа"""
        try:
            import winsound
            
            # Настройки звуковых сигналов
            beep_settings = {
                'beep_high': (1000, 100),    # Высокий тон, 100мс
                'beep_medium': (800, 80),     # Средний тон, 80мс
                'beep_low': (600, 60),        # Низкий тон, 60мс
            }
            
            if sound_type in beep_settings:
                frequency, duration = beep_settings[sound_type]
                winsound.Beep(frequency, duration)
            else:
                # По умолчанию средний сигнал
                winsound.Beep(800, 80)
                
        except ImportError:
            # Если winsound недоступен, используем системный звук
            try:
                import os
                os.system('echo ')  # Системный звуковой сигнал
            except:
                pass
        except Exception as e:
            print(f"Ошибка воспроизведения beep: {e}")

    def on_result(self, text):
        # Проверяем, не обрабатывается ли уже AI запрос
        if self.is_processing_ai:
            self.log('AI: Сейчас обрабатываю предыдущий запрос, подождите...')
            return
        
        self.log('Вы: ' + text)
        text_lower = text.lower()
        found_cmd = None
        
        # Проверяем стандартные команды
        for syn, main_cmd in COMMAND_SYNONYMS.items():
            if syn in text_lower:
                found_cmd = main_cmd
                break
        if not found_cmd:
            for cmd in COMMANDS.keys():
                if cmd in text_lower:
                    found_cmd = cmd
                    break
        
        if found_cmd:
            # Обработка стандартных команд
            resp = COMMANDS.get(found_cmd)
            
            # Получаем фразу подтверждения
            confirmation = COMMAND_CONFIRMATIONS.get(found_cmd, "Выполняю команду.")
            
            if found_cmd == 'время':
                now = datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')
                self.log('Ассистент: ' + confirmation)
                speak_text(confirmation)
                time.sleep(0.5)  # Небольшая пауза
                self.log('Ассистент: ' + now)
                speak_text(now)
                self.play_command_voice(found_cmd)
                with open('current_time.txt', 'w', encoding='utf-8') as f:
                    f.write(f'Текущее время: {now}')
                os.system('notepad current_time.txt')
                return
            elif found_cmd == 'шутка':
                joke = random.choice(JOKES)
                self.log('Ассистент: ' + confirmation)
                speak_text(confirmation)
                time.sleep(0.5)
                self.log('Ассистент: ' + joke)
                speak_text(joke)
                self.play_command_voice('default')
                return
            elif found_cmd == 'благодарность':
                thanks = random.choice(THANKS_RESPONSES)
                self.log('Ассистент: ' + thanks)
                speak_text(thanks)
                self.play_command_voice('default')
                return
            elif found_cmd == 'оскорбление':
                insult = random.choice(INSULT_RESPONSES)
                self.log('Ассистент: ' + insult)
                speak_text(insult)
                self.play_command_voice('default')
                return
            elif isinstance(resp, str):
                self.log('Ассистент: ' + resp)
                speak_text(resp)
                self.play_command_voice(found_cmd)
                if found_cmd == 'пока':
                    self.toggle_assistant()
                return
            elif isinstance(resp, tuple):
                msg, action = resp
                if msg:
                    self.log('Ассистент: ' + msg)
                    speak_text(msg)
                self.play_command_voice(found_cmd)
                if action:
                    action()
                return
        else:
            # Если команда не найдена, пробуем AI
            if self.ollama_available and len(text.strip()) > 3:
                self.log('AI: Обрабатываю запрос через Gemma3...')
                speak_text("Обрабатываю ваш запрос через искусственный интеллект")
                
                # Отключаем распознавание голоса
                self.is_processing_ai = True
                self.status_label.config(text='AI обрабатывает запрос...', fg='orange')
                
                try:
                    # Обрабатываем в отдельном потоке
                    def process_ai_request():
                        try:
                            response = ask_ollama(text)
                            self.log('AI: ' + response)
                            speak_text(response)
                        except Exception as e:
                            error_msg = f"Ошибка AI: {str(e)}"
                            self.log(error_msg)
                            speak_text("Извините, произошла ошибка при обработке запроса")
                        finally:
                            # Включаем распознавание голоса обратно
                            self.is_processing_ai = False
                            self.status_label.config(text='Ассистент работает', fg='green')
                    
                    threading.Thread(target=process_ai_request, daemon=True).start()
                    return
                except Exception as e:
                    self.log(f'Ошибка AI: {e}')
                    speak_text("Извините, не удалось обработать запрос")
                    self.is_processing_ai = False
                    self.status_label.config(text='Ассистент работает', fg='green')
                    return
        
        # Если ничего не найдено
        not_found_msg = 'Команда не распознана. Попробуйте задать вопрос или использовать стандартные команды.'
        self.log('Ассистент: ' + not_found_msg)
        speak_text(not_found_msg)
        self.play_command_voice('default')

    def on_error(self, e):
        self.log(f'Ошибка: {e}')
        messagebox.showerror('Ошибка', f'Произошла ошибка:\n{e}\nПодробности в error_log.txt')





# --- Точка входа ---
def main():
    try:
        root = tk.Tk()
        app = AssistantGUI(root)
        root.mainloop()
    except Exception as e:
        log_error(e)
        messagebox.showerror('Ошибка', f'Произошла ошибка:\n{e}\nПодробности в error_log.txt')

if __name__ == '__main__':
    main() 