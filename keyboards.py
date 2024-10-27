from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_user_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    keyboard.add(KeyboardButton("🔍 Проверить профиль"))
    keyboard.add(KeyboardButton("💡 Помощь"), KeyboardButton("ℹ️ О боте"))
    return keyboard

def get_admin_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    keyboard.add(KeyboardButton("💡 Помощь"), KeyboardButton("ℹ️ О боте"))
    keyboard.add(KeyboardButton("⚙️ Настройки"), KeyboardButton("🔄 Перезагрузить шаблоны"))
    keyboard.add(KeyboardButton("💰 Управление выплатами"))
    return keyboard

def get_payment_management_kb():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        InlineKeyboardButton("💰 Задать сумму выплаты", callback_data="approve_payment"),
        InlineKeyboardButton("❌ Отклонить", callback_data="reject_payment")
    )
    return keyboard

def get_settings_kb(current_mode):
    keyboard = InlineKeyboardMarkup()
    mode_text = "Переключить на URL" if current_mode == "exact" else "Переключить на точную"
    keyboard.add(InlineKeyboardButton(mode_text, callback_data="toggle_check_mode"))
    return keyboard

def get_profile_check_kb():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔄 Проверить снова", callback_data="recheck"))
    return keyboard

def get_back_kb():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
    return keyboard

def get_payment_request_kb():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📝 Отправить заявку на выплату", callback_data="submit_payment_request"))
    return keyboard

def get_admin_payments_kb(applications):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for app in applications:
        buttons.append(InlineKeyboardButton(
            f"ID: {app[1]}",
            callback_data=f"approve_payment_{app[1]}"
        ))
    keyboard.add(*buttons)
    return keyboard
