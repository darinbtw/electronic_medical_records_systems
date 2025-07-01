
// Улучшенная обработка дат в веб-интерфейсе
function safeDateFormat(dateString) {
    if (!dateString || dateString === 'null' || dateString === 'undefined') {
        return 'не указана';
    }
    
    try {
        // Если уже в русском формате
        if (dateString.includes('.')) {
            return dateString;
        }
        
        // Если в ISO формате
        let date;
        if (dateString.includes('T')) {
            date = new Date(dateString);
        } else if (dateString.includes('-')) {
            // YYYY-MM-DD формат
            const parts = dateString.split('-');
            date = new Date(parts[0], parts[1] - 1, parts[2]);
        } else {
            date = new Date(dateString);
        }
        
        // Проверяем валидность
        if (isNaN(date.getTime())) {
            console.warn('Invalid date:', dateString);
            return dateString;
        }
        
        // Форматируем в русском стиле
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        
        return `${day}.${month}.${year}`;
        
    } catch (error) {
        console.error('Date formatting error:', error);
        return dateString || 'ошибка даты';
    }
}

// Функция для обновления всех дат на странице
function fixAllDatesOnPage() {
    // Находим все элементы с датами и исправляем их
    document.querySelectorAll('[data-date]').forEach(element => {
        const dateValue = element.getAttribute('data-date');
        element.textContent = safeDateFormat(dateValue);
    });
    
    console.log('✅ Все даты на странице исправлены');
}

// Автоматически исправляем даты при загрузке
document.addEventListener('DOMContentLoaded', fixAllDatesOnPage);
