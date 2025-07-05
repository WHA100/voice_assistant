#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyttsx3
import time

def test_tts():
    """Тестирование улучшенного TTS"""
    try:
        print("🎤 Тестирование TTS с улучшенными настройками")
        print("=" * 50)
        
        # Инициализация TTS
        engine = pyttsx3.init()
        
        # Получаем список голосов
        voices = engine.getProperty('voices')
        print(f"📋 Найдено голосов: {len(voices)}")
        
        # Показываем доступные голоса
        for i, voice in enumerate(voices):
            print(f"  {i+1}. {voice.name} ({voice.id})")
        
        # Ищем лучший русский голос
        best_voice = None
        for voice in voices:
            voice_name = voice.name.lower()
            voice_id = voice.id.lower()
            
            if 'russian' in voice_name or 'ru' in voice_id or 'русский' in voice_name:
                best_voice = voice.id
                print(f"✅ Найден русский голос: {voice.name}")
                break
            elif 'english' in voice_name or 'en' in voice_id:
                if not best_voice:
                    best_voice = voice.id
                    print(f"🔤 Найден английский голос: {voice.name}")
        
        # Устанавливаем голос
        if best_voice:
            engine.setProperty('voice', best_voice)
            print(f"🎯 Установлен голос: {best_voice}")
        
        # Оптимальные настройки
        engine.setProperty('rate', 140)      # Скорость речи
        engine.setProperty('volume', 0.9)    # Громкость
        
        print(f"⚙️  Скорость речи: {engine.getProperty('rate')}")
        print(f"🔊 Громкость: {engine.getProperty('volume')}")
        
        # Тестовые фразы
        test_phrases = [
            "Привет! Я голосовой ассистент с улучшенным качеством речи.",
            "Теперь я говорю более красиво и естественно.",
            "Мой голос стал более приятным для восприятия.",
            "Спасибо за использование нашего ассистента!"
        ]
        
        print("\n🎵 Тестирование речи:")
        for i, phrase in enumerate(test_phrases, 1):
            print(f"\n{i}. Произношу: {phrase}")
            engine.say(phrase)
            engine.runAndWait()
            time.sleep(0.5)
        
        print("\n✅ Тест TTS завершен успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка TTS: {e}")
        return False

if __name__ == "__main__":
    test_tts() 