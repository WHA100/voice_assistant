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
from playsound import playsound
import traceback
import random
import ctypes
import subprocess
import time
import pyautogui

# --- Путь к модели Vosk (скачайте и распакуйте модель в папку 'vosk-model-small-ru') ---
VOSK_MODEL_PATH = 'vosk-model-small-ru'

# --- Звуки для команд ---
COMMAND_SOUNDS = {
    'привет': ['voice/Джарвис - приветствие.wav', 'voice/Доброе утро.wav'],
    'браузер': ['voice/downloading_sir.wav'],
    'ютуб': ['voice/downloading_sir.wav'],
    'блокнот': ['voice/downloading_sir.wav'],
    'калькулятор': ['voice/downloading_sir.wav'],
    'проводник': ['voice/downloading_sir.wav'],
    'выключи компьютер': ['voice/Проверка завершена.wav'],
    'заблокируй экран': ['voice/Проверка завершена.wav'],
    'панель управления': ['voice/downloading_sir.wav'],
    'время': ['voice/request_completed.wav'],
    'пока': ['voice/Поздравляю сэр.wav', 'voice/Yes_sir.wav'],
    'default': [
        'voice/Yes_sir.wav',
        'voice/Поздравляю сэр.wav',
        'voice/Проверка завершена.wav',
        'voice/Начинаю диагностику системы.wav',
        'voice/Мы подключены и готовы.wav',
        'voice/Я перезагрузился сэр.wav',
    ],
    'скриншот': ['voice/request_completed.wav'],
    'звук выкл': ['voice/request_completed.wav'],
    'звук вкл': ['voice/request_completed.wav'],
    'громче': ['voice/request_completed.wav'],
    'тише': ['voice/request_completed.wav'],
    'звук 20': ['voice/request_completed.wav'],
    'звук 50': ['voice/request_completed.wav'],
    'звук 80': ['voice/request_completed.wav'],
    'звук 100': ['voice/request_completed.wav'],
    'язык': ['voice/request_completed.wav'],
    'язык русский': ['voice/request_completed.wav'],
    'язык английский': ['voice/request_completed.wav'],
    'свернуть окна': ['voice/request_completed.wav'],
    'корзина': ['voice/request_completed.wav'],
    'буфер обмена': ['voice/request_completed.wav'],
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

# --- Команды ---
COMMANDS = {
    'привет': 'Привет! Чем могу помочь?',
    'браузер': ('Открываю браузер.', lambda: webbrowser.open('https://www.google.com')),
    'ютуб': ('Открываю YouTube.', lambda: webbrowser.open('https://www.youtube.com')),
    'блокнот': ('Открываю Блокнот.', lambda: os.system('notepad')),
    'калькулятор': ('Открываю калькулятор.', lambda: os.system('start calc')),
    'проводник': ('Открываю проводник.', lambda: os.system('explorer')),
    'выключи компьютер': ('Выключаю компьютер.', lambda: os.system('shutdown /s /t 5')),
    'заблокируй экран': ('Блокирую экран.', lambda: os.system('rundll32.exe user32.dll,LockWorkStation')),
    'панель управления': ('Открываю панель управления.', lambda: os.system('control')),
    'время': (None, None),
    'пока': 'До свидания! Хорошего дня!',
    'шутка': (None, None),
    'благодарность': (None, None),
    'оскорбление': (None, None),
    'музыка': ('Открываю музыку (заглушка).', None),
    'стим': ('Открываю Steam (заглушка).', None),
    'диспетчер задач': ('Открываю диспетчер задач.', lambda: os.system('taskmgr')),
    'буфер обмена': ('Открываю буфер обмена.', lambda: os.system('cmd /c "echo off | clip"')),
    'корзина': ('Очищаю корзину (заглушка).', None),
    'скриншот': ('Делаю скриншот (заглушка).', None),
    'звук выкл': ('Выключаю звук (заглушка).', None),
    'звук вкл': ('Включаю звук (заглушка).', None),
    'громче': ('Делаю громче (заглушка).', None),
    'тише': ('Делаю тише (заглушка).', None),
    'язык': ('Переключаю язык ввода (заглушка).', None),
    'язык русский': ('Переключаю язык на русский (заглушка).', None),
    'язык английский': ('Переключаю язык на английский (заглушка).', None),
    'загрузки': ('Открываю папку Загрузки.', lambda: os.system('explorer shell:Downloads')),
    'документы': ('Открываю папку Документы.', lambda: os.system('explorer shell:Personal')),
    'рабочий стол': ('Открываю рабочий стол.', lambda: os.system('explorer shell:Desktop')),
    'поиск': ('Открываю браузер для поиска (заглушка).', lambda: webbrowser.open('https://www.google.com')),
    'погода': ('Погода сейчас недоступна (заглушка).', None),
    'системная информация': ('Показываю системную информацию (заглушка).', None),
    'свернуть окна': ('Сворачиваю все окна (заглушка).', None),
    'игровой режим': ('Включаю игровой режим (открываю Steam).', lambda: os.startfile(r'C:\Program Files (x86)\Steam\steam.exe')),
    'рабочий режим': ('Возвращаюсь в рабочий режим (закрываю Steam).', lambda: os.system('taskkill /IM steam.exe /F')),
    'звук 20': ('Устанавливаю громкость на 20%.', lambda: set_volume(20)),
    'звук 50': ('Устанавливаю громкость на 50%.', lambda: set_volume(50)),
    'звук 80': ('Устанавливаю громкость на 80%.', lambda: set_volume(80)),
    'звук 100': ('Устанавливаю громкость на 100%.', lambda: set_volume(100)),
}

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
        self.samplerate = int(sd.query_devices(device, 'input')['default_samplerate'])
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
        self.root.title('Голосовой помощник (Vosk)')
        self.root.geometry('650x500')
        self.root.resizable(False, False)
        self.assistant = None
        self.is_listening = False

        self.status_label = tk.Label(root, text='Ассистент выключен', fg='red', font=('Arial', 12, 'bold'))
        self.status_label.pack(pady=(10, 0))

        self.mic_label = tk.Label(root, text='Выберите микрофон:', font=('Arial', 10))
        self.mic_label.pack(pady=(10, 0))
        self.mic_combo = ttk.Combobox(root, state='readonly', width=60)
        self.mic_combo.pack(pady=5)
        self.refresh_mics()

        self.start_button = tk.Button(root, text='Включить ассистента', command=self.toggle_assistant, font=('Arial', 14), width=25, bg='#4CAF50', fg='white')
        self.start_button.pack(pady=10)

        self.log_text = ScrolledText(root, width=80, height=20, state='disabled', font=('Consolas', 11))
        self.log_text.pack(padx=10, pady=10)

        self.log('Добро пожаловать! Выберите микрофон, затем нажмите "Включить ассистента".')

    def refresh_mics(self):
        devices = sd.query_devices()
        input_devices = [f"{i}: {d['name']}" for i, d in enumerate(devices) if d['max_input_channels'] > 0]
        self.mic_combo['values'] = input_devices
        if input_devices:
            self.mic_combo.current(0)

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
        sounds = COMMAND_SOUNDS.get(cmd, COMMAND_SOUNDS['default'])
        sound = random.choice(sounds)
        try:
            playsound(sound)
        except Exception:
            pass

    def on_result(self, text):
        self.log('Вы: ' + text)
        text_lower = text.lower()
        found_cmd = None
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
            resp = COMMANDS.get(found_cmd)
            if found_cmd == 'время':
                now = datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')
                self.log('Ассистент: ' + now)
                self.play_command_voice(found_cmd)
                with open('current_time.txt', 'w', encoding='utf-8') as f:
                    f.write(f'Текущее время: {now}')
                os.system('notepad current_time.txt')
                return
            elif found_cmd == 'шутка':
                joke = random.choice(JOKES)
                self.log('Ассистент: ' + joke)
                self.play_command_voice('default')
                return
            elif found_cmd == 'благодарность':
                thanks = random.choice(THANKS_RESPONSES)
                self.log('Ассистент: ' + thanks)
                self.play_command_voice('default')
                return
            elif found_cmd == 'оскорбление':
                insult = random.choice(INSULT_RESPONSES)
                self.log('Ассистент: ' + insult)
                self.play_command_voice('default')
                return
            elif isinstance(resp, str):
                self.log('Ассистент: ' + resp)
                self.play_command_voice(found_cmd)
                if found_cmd == 'пока':
                    self.toggle_assistant()
                return
            elif isinstance(resp, tuple):
                msg, action = resp
                if msg:
                    self.log('Ассистент: ' + msg)
                self.play_command_voice(found_cmd)
                if action:
                    action()
                return
        self.log('Ассистент: Команда не распознана.')
        self.play_command_voice('default')

    def on_error(self, e):
        self.log(f'Ошибка: {e}')
        messagebox.showerror('Ошибка', f'Произошла ошибка:\n{e}\nПодробности в error_log.txt')

# --- Реальные действия для команд ---
def mute_volume():
    pyautogui.press('volumemute')
def unmute_volume():
    pyautogui.press('volumemute')  # Обычно это же действие
    # Можно добавить проверку состояния, если нужно

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
    playsound('voice/request_completed.wav')
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

COMMANDS.update({
    'звук выкл': ('Выключаю звук.', mute_volume),
    'звук вкл': ('Включаю звук.', unmute_volume),
    'громче': ('Делаю громче.', volume_up),
    'тише': ('Делаю тише.', volume_down),
    'скриншот': ('Делаю скриншот.', take_screenshot),
    'свернуть окна': ('Сворачиваю все окна.', minimize_all_windows),
    'язык': ('Переключаю язык ввода.', switch_language),
    'язык русский': ('Переключаю язык на русский.', lambda: switch_language('ru')),
    'язык английский': ('Переключаю язык на английский.', lambda: switch_language('en')),
    'буфер обмена': ('Открываю буфер обмена.', open_clipboard),
    'корзина': ('Очищаю корзину.', empty_recycle_bin),
    'звук 20': ('Устанавливаю громкость на 20%.', lambda: set_volume(20)),
    'звук 50': ('Устанавливаю громкость на 50%.', lambda: set_volume(50)),
    'звук 80': ('Устанавливаю громкость на 80%.', lambda: set_volume(80)),
    'звук 100': ('Устанавливаю громкость на 100%.', lambda: set_volume(100)),
})

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