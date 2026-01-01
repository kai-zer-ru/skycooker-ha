#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к мультиварке RMC-M40S
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'skycooker'))

from cooker_connection import CookerConnection
from skycooker import SkyCooker

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_connection():
    """Тест подключения к мультиварке"""
    print("=== Тест подключения к мультиварке RMC-M40S ===")
    
    # Замените на реальный MAC-адрес вашей мультиварки
    mac_address = "DA:D8:9F:9E:0B:4C"  # Замените на реальный MAC
    
    # Ключ аутентификации (обычно 8 байт)
    key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07]  # Стандартный ключ
    
    # Модель мультиварки
    model = "RMC-M40S"
    
    try:
        # Создаем соединение
        cooker = CookerConnection(
            mac=mac_address,
            key=key,
            persistent=True,
            model=model
        )
        
        print(f"Создано соединение для {model}")
        print(f"MAC-адрес: {mac_address}")
        print(f"Ключ: {[hex(b) for b in key]}")
        
        # Попытка подключения
        print("\nПопытка подключения...")
        await cooker.update()
        
        if cooker.available:
            print("✓ Подключение успешно!")
            print(f"  Версия прошивки: {cooker.sw_version}")
            print(f"  Текущая температура: {cooker.current_temp}")
            print(f"  Текущий режим: {cooker.current_mode}")
            print(f"  Целевая температура: {cooker.target_temp}")
            print(f"  Целевой режим: {cooker.target_mode}")
            print(f"  Успешность подключений: {cooker.success_rate}%")
        else:
            print("✗ Подключение не удалось")
            print(f"  Причина: {cooker._last_connect_ok=}, {cooker._last_auth_ok=}")
            
    except Exception as e:
        print(f"✗ Ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'cooker' in locals():
            await cooker.disconnect()
            cooker.stop()

async def scan_devices():
    """Сканирование Bluetooth устройств"""
    print("\n=== Сканирование Bluetooth устройств ===")
    
    try:
        from bleak import BleakScanner
        from homeassistant.components import bluetooth
        
        print("Поиск устройств...")
        devices = await BleakScanner.discover(timeout=10.0)
        
        print(f"Найдено {len(devices)} устройств:")
        for device in devices:
            if device.name and (device.name.startswith("RMC-") or device.name.startswith("RK-")):
                print(f"  ✓ {device.address} - {device.name}")
            else:
                print(f"    {device.address} - {device.name}")
                
    except Exception as e:
        print(f"Ошибка сканирования: {e}")

async def main():
    """Главная функция"""
    print("SkyCooker HA - Тест подключения")
    print("=" * 50)
    
    # Сначала сканируем устройства
    await scan_devices()
    
    # Затем пробуем подключиться
    await test_connection()
    
    print("\nТест завершен")

if __name__ == "__main__":
    asyncio.run(main())