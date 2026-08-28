#!/usr/bin/env python3
# coding: utf-8

"""
Кастомный логер для библиотеки SkyCooker.
"""

import logging
import sys


class SkyCookerLogger:
    """
    Кастомный логер для библиотеки SkyCooker.
    """
    
    def __init__(self, name="skycooker"):
        """
        Инициализация логера.
        
        Args:
            name (str): Имя логера.
        """
        self.logger = logging.getLogger(name)
        # Проверяем, есть ли уже обработчики у логера
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            
            # Создаем форматтер
            formatter = logging.Formatter(
                '%(asctime)s, %(filename)-24s:%(lineno)-4d, %(levelname)s, %(message)s'
            )
            
            # Создаем обработчик для вывода в консоль
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(formatter)
            
            # Добавляем обработчик к логеру
            self.logger.addHandler(handler)
    
    def get_logger(self):
        """
        Получение экземпляра логера.
        
        Returns:
            logging.Logger: Экземпляр логера.
        """
        return self.logger


# Создаем глобальный логер для библиотеки
skycooker_logger = SkyCookerLogger().get_logger()