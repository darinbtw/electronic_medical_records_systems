"+7 (999) 123-45-67"    ->  "79991234567"
"8-999-123-45-67"       ->  "89991234567"  
"+7 999 123 45 67"      ->  "79991234567"
"(999) 123-45-67"       ->  "9991234567"

digits = "79991234567"

digits[1:4]   -> "999"     # символы с 1 по 3
digits[4:7]   ->  "123"    # символы с 4 по 6 
digits[7:9]   ->  "45"     # символы с 7 по 8
digits[9:11]  ->  "67"     # символы с 9 по 10

# Результат: "+7 (999) 123-45-67"