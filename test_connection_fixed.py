#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к мультиварке
"""

import sys
import os

# Добавляем путь к custom_components в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

# Теперь можно импортировать
from skycooker.cooker_connection import CookerConnection
from skycooker.const import *

async def test_connection():
    """Тест подключения к мультиварке"""
    
    # Пример использования
    mac_address = "DA:D8:9F:9E:0B:4C"  # Замените на реальный MAC адрес
    auth_key = "00000000"  # Замените на реальный ключ
    
    print(f"Testing connection to {mac_address}...")
    
    try:
        # Создаем объект подключения
        connection = CookerConnection(
            mac=mac_address,
            key=auth_key,
            persistent=False,
            adapter=None,
            hass=None,
            model="RMC-M40S"
        )
        
        print("Connection object created successfully")
        print(f"Device MAC: {connection._mac}")
        print(f"Device model: {connection.model}")
        print(f"Connection status: Not connected (expected)")
        
        # Обратите внимание: для реального подключения нужен hass объект
        # и работающий Home Assistant с Bluetooth интеграцией
        print("\nNote: Full connection test requires running Home Assistant")
        print("This test only verifies module import and object creation")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    
    print("SkyCooker Connection Test")
    print("=" * 40)
    
    # Запускаем асинхронный тест
    result = asyncio.run(test_connection())
    
    if result:
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)