Примеры проверки:
validate_phone("+7 (999) 123-45-67")  # ✅ True (11 цифр)
validate_phone("8-999-123-45-67")     # ✅ True (11 цифр)
validate_phone("123-456-7890")        # ✅ True (10 цифр)
validate_phone("123")                 # ❌ False (3 цифры - мало)
validate_phone("12345678901234567")   # ❌ False (17 цифр - много)