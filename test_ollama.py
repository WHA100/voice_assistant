#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_ollama():
    """Тестирование подключения к Ollama"""
    try:
        # Проверка доступности сервиса
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            print("✅ Ollama сервис доступен")
            
            # Тестовый запрос к Gemma3
            payload = {
                "model": "gemma3",
                "prompt": "Привет! Как дела?",
                "stream": False,
                "options": {
                    "num_predict": 100,
                    "temperature": 0.7
                }
            }
            
            print("🔄 Отправляю тестовый запрос к Gemma3...")
            response = requests.post('http://localhost:11434/api/generate', json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', 'Нет ответа')
                print(f"✅ Ответ от Gemma3: {answer}")
                return True
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                return False
        else:
            print(f"❌ Ollama сервис недоступен: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Тестирование Ollama + Gemma3")
    print("=" * 40)
    test_ollama() 