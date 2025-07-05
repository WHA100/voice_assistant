#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import edge_tts
import tempfile
import os
import pygame

def test_edge_tts_voice():
    """Тест голоса edge-tts"""
    print("🎤 Тестирование edge-tts голоса")
    print("=" * 40)
    
    test_phrases = [
        "Выполняю.",
        "Выполняю.",
        "Выполняю.",
        "Обрабатываю ваш запрос через искусственный интеллект",
        "Выполняю."
    ]
    
    async def speak_phrases():
        pygame.mixer.init()
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"{i}. Произношу: {phrase}")
            
            try:
                temp_filename = tempfile.mktemp(suffix='.mp3')
                communicate = edge_tts.Communicate(phrase, "ru-RU-SvetlanaNeural")
                await communicate.save(temp_filename)
                
                pygame.mixer.music.load(temp_filename)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                
                try:
                    os.unlink(temp_filename)
                except:
                    pass
                
                await asyncio.sleep(1)  # Пауза между фразами
                
            except Exception as e:
                print(f"Ошибка: {e}")
    
    asyncio.run(speak_phrases())
    print("\n✅ Тест голоса завершен!")

def test_command_confirmations():
    """Тест фраз подтверждения команд"""
    print("\n📋 Фразы подтверждения команд:")
    print("=" * 40)
    
    confirmations = [
        "Выполняю.",
        "Выполняю.",
        "Выполняю.",
        "Выполняю.",
        "Выполняю.",
        "Выполняю.",
        "Выполняю.",
        "Выполняю.",
        "Выполняю.",
        "Выполняю."
    ]
    
    for i, confirmation in enumerate(confirmations, 1):
        print(f"{i}. {confirmation}")

if __name__ == "__main__":
    print("🧪 Тестирование обновленного голосового ассистента")
    print("=" * 50)
    
    # Тест фраз подтверждения
    test_command_confirmations()
    
    # Тест голоса
    print("\n" + "=" * 50)
    test_edge_tts_voice()
    
    print("\n🎉 Все тесты завершены!")
    print("\n📝 Что изменилось:")
    print("• Добавлены фразы подтверждения команд")
    print("• Отключение распознавания во время AI запросов")
    print("• Улучшенный голос через edge-tts")
    print("• Предотвращение конфликтов команд и ответов") 