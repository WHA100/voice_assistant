#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import tempfile
import os
import time
from gtts import gTTS
import edge_tts
import pyttsx3
import pygame

class TTSComparison:
    def __init__(self):
        self.test_text = "Привет! Я тестирую разные системы синтеза речи."
        pygame.mixer.init()
    
    def test_pyttsx3(self):
        """Тест pyttsx3 (локальный TTS)"""
        print("🎤 Тестирование pyttsx3...")
        try:
            engine = pyttsx3.init()
            
            # Настройка русского голоса
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'russian' in voice.name.lower() or 'ru' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            engine.setProperty('rate', 140)
            engine.setProperty('volume', 0.9)
            
            start_time = time.time()
            engine.say(self.test_text)
            engine.runAndWait()
            duration = time.time() - start_time
            
            print(f"✅ pyttsx3: {duration:.2f} сек")
            return True
        except Exception as e:
            print(f"❌ pyttsx3 ошибка: {e}")
            return False
    
    def test_gtts(self):
        """Тест gTTS (Google TTS)"""
        print("🌐 Тестирование gTTS (Google)...")
        try:
            start_time = time.time()
            
            # Создаем временный файл
            temp_filename = tempfile.mktemp(suffix='.mp3')
            
            # Генерируем речь
            tts = gTTS(text=self.test_text, lang='ru', slow=False)
            tts.save(temp_filename)
            
            # Воспроизводим
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # Ждем окончания воспроизведения
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            duration = time.time() - start_time
            
            # Удаляем временный файл
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            print(f"✅ gTTS: {duration:.2f} сек")
            return True
        except Exception as e:
            print(f"❌ gTTS ошибка: {e}")
            return False
    
    async def test_edge_tts(self):
        """Тест edge-tts (Microsoft Edge TTS)"""
        print("🔗 Тестирование edge-tts (Microsoft)...")
        try:
            start_time = time.time()
            
            # Создаем временный файл
            temp_filename = tempfile.mktemp(suffix='.mp3')
            
            # Генерируем речь
            communicate = edge_tts.Communicate(self.test_text, "ru-RU-SvetlanaNeural")
            await communicate.save(temp_filename)
            
            # Воспроизводим
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # Ждем окончания воспроизведения
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            duration = time.time() - start_time
            
            # Удаляем временный файл
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            print(f"✅ edge-tts: {duration:.2f} сек")
            return True
        except Exception as e:
            print(f"❌ edge-tts ошибка: {e}")
            return False
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("🧪 Сравнение TTS библиотек")
        print("=" * 50)
        print(f"Тестовый текст: {self.test_text}")
        print()
        
        # Тест pyttsx3
        self.test_pyttsx3()
        await asyncio.sleep(1)
        
        # Тест gTTS
        self.test_gtts()
        await asyncio.sleep(1)
        
        # Тест edge-tts
        await self.test_edge_tts()
        
        print("\n" + "=" * 50)
        print("📊 Результаты:")
        print("• pyttsx3: Локальный, быстрый, но качество среднее")
        print("• gTTS: Онлайн, хорошее качество, требует интернет")
        print("• edge-tts: Онлайн, отличное качество, требует интернет")

if __name__ == "__main__":
    comparison = TTSComparison()
    asyncio.run(comparison.run_all_tests()) 