#!/bin/bash

# Скрипт для коммита и пуша изменений в репозиторий

echo "=== SkyCooker HA - Git Commit & Push ==="

# Проверяем, что мы в git репозитории
if [ ! -d ".git" ]; then
    echo "❌ Ошибка: Это не git репозиторий"
    echo "Пожалуйста, инициализируйте git репозиторий:"
    echo "  git init"
    echo "  git remote add origin <ваш_репозиторий>"
    exit 1
fi

# Проверяем статус репозитория
echo "🔍 Проверка статуса репозитория..."
git status

echo ""
echo "📝 Добавление изменений в индекс..."
git add .

# Проверяем, есть ли изменения для коммита
if git diff --cached --quiet; then
    echo "⚠️  Нет изменений для коммита"
    exit 0
fi

echo ""
echo "🎯 Создание коммита..."

# Формируем сообщение коммита
COMMIT_MESSAGE="feat: Полная поддержка мультиварки RMC-M40S

- Добавлена поддержка 11 программ приготовления
- Реализовано управление температурой (35-120°C) и таймером
- Исправлены проблемы с Bluetooth подключением
- Добавлены новые entity для мультиварки
- Создана полная документация и тесты
- Оптимизировано подключение для стабильной работы

#skycooker #rmc-m40s #homeassistant"

git commit -m "$COMMIT_MESSAGE"

if [ $? -eq 0 ]; then
    echo "✅ Коммит успешно создан"
else
    echo "❌ Ошибка при создании коммита"
    exit 1
fi

echo ""
echo "🚀 Выполнение пуша в удаленный репозиторий..."

# Пытаемся сделать пуш
git push

if [ $? -eq 0 ]; then
    echo "✅ Пуш выполнен успешно"
else
    echo "❌ Ошибка при пушe"
    echo "Возможные причины:"
    echo "1. Нет подключения к интернету"
    echo "2. Нет доступа к удаленному репозиторию"
    echo "3. Нужна аутентификация"
    echo ""
    echo "Попробуйте:"
    echo "  git remote -v  # проверить remote"
    echo "  git remote add origin <url>  # добавить remote если нет"
    echo "  git push -u origin main  # первый пуш с установкой upstream"
    exit 1
fi

echo ""
echo "🎉 Все изменения успешно закоммичены и запушены!"
echo ""
echo "Статус репозитория:"
git status
echo ""
echo "Последние коммиты:"
git log --oneline -5