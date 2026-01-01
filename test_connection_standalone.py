#!/usr/bin/env python3
"""
Standalone тестовый скрипт для проверки подключения к мультиварке RMC-M40S
Не требует установки Home Assistant и его зависимостей
"""

import asyncio
import logging
import sys
import os
import subprocess

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Проверяем наличие необходимых зависимостей"""
    try:
        import bleak
        print("✓ bleak установлен")
    except ImportError:
        print("✗ bleak не установлен.")
        print("Для установки в HAOS выполните:")
        print("apk add py3-bleak")
        return False
    
    try:
        import bleak_retry_connector
        print("✓ bleak_retry_connector установлен")
    except ImportError:
        print("✗ bleak_retry_connector не установлен.")
        print("Для установки в HAOS выполните:")
        print("apk add py3-bleak-retry-connector")
        return False
    
    return True

async def scan_devices():
    """Сканирование Bluetooth устройств"""
    print("\n=== Сканирование Bluetooth устройств ===")
    
    try:
        from bleak import BleakScanner
        
        print("Поиск устройств...")
        devices = await BleakScanner.discover(timeout=10.0)
        
        print(f"Найдено {len(devices)} устройств:")
        cooker_devices = []
        for device in devices:
            if device.name and (device.name.startswith("RMC-") or device.name.startswith("RK-")):
                print(f"  ✓ {device.address} - {device.name}")
                cooker_devices.append(device)
            else:
                print(f"    {device.address} - {device.name}")
        
        return cooker_devices
                
    except Exception as e:
        print(f"Ошибка сканирования: {e}")
        return []

async def test_connection_standalone():
    """Тест подключения к мультиварке без зависимостей HA"""
    print("=== Тест подключения к мультиварке RMC-M40S (Standalone) ===")
    
    # Сначала сканируем устройства
    cooker_devices = await scan_devices()
    
    if not cooker_devices:
        print("✗ Не найдено устройств мультиварки. Убедитесь, что:")
        print("  1. Мультиварка включена и в режиме сопряжения")
        print("  2. Bluetooth адаптер работает")
        print("  3. Мультиварка находится в зоне действия")
        return
    
    # Используем первое найденное устройство
    cooker_device = cooker_devices[0]
    mac_address = cooker_device.address
    
    print(f"\nИспользуем устройство: {mac_address} - {cooker_device.name}")
    
    # Ключ аутентификации (обычно 8 байт)
    key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07]  # Стандартный ключ
    
    try:
        from bleak_retry_connector import establish_connection
        from bleak import BleakClient
        
        print(f"\nПопытка подключения к {mac_address}...")
        
        # Создаем клиент
        client = await establish_connection(
            BleakClient,
            cooker_device,
            cooker_device.name or "Unknown Device",
            max_attempts=3
        )
        
        if client.is_connected:
            print("✓ Подключение к Bluetooth успешно!")
            
            # Получаем сервисы
            services = await client.get_services()
            print(f"Найдено сервисов: {len(services)}")
            
            # Ищем нужный сервис
            cooker_service = None
            for service in services:
                if str(service.uuid).lower() == "6e400001-b5a3-f393-e0a9-e50e24dcca9e":
                    cooker_service = service
                    break
            
            if cooker_service:
                print("✓ Найден сервис мультиварки")
                
                # Получаем характеристики
                characteristics = cooker_service.characteristics
                print(f"Найдено характеристик: {len(characteristics)}")
                
                for char in characteristics:
                    print(f"  Характеристика: {char.uuid} - {char.properties}")
            else:
                print("✗ Сервис мультиварки не найден")
            
            await client.disconnect()
            print("✓ Отключено")
        else:
            print("✗ Подключение не удалось")
            
    except Exception as e:
        print(f"✗ Ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Главная функция"""
    print("SkyCooker - Standalone Тест подключения")
    print("=" * 50)
    
    # Проверяем зависимости
    if not check_dependencies():
        print("\nУстановите зависимости и перезапустите тест")
        return
    
    # Тестируем подключение
    await test_connection_standalone()
    
    print("\nТест завершен")

if __name__ == "__main__":
    asyncio.run(main())