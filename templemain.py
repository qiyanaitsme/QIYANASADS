from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import BOT_TOKEN, ZELENKA_TOKEN, ADMIN_IDS
from keyboards import (
    get_user_kb, get_admin_kb, get_settings_kb, get_profile_check_kb,
    get_back_kb, get_payment_request_kb, get_admin_payments_kb, get_payment_management_kb
)
from text_utils import normalize_text, check_status, extract_user_id, check_pinned_post
from api_client import ZelenkaAPI
from settings_manager import SettingsManager
from database import Database
from payment_api import PaymentAPI

class ProfileCheck(StatesGroup):
    waiting_for_id = State()

class PaymentStates(StatesGroup):
    waiting_for_amount = State()


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
api = ZelenkaAPI(ZELENKA_TOKEN)
settings_manager = SettingsManager()
db = Database()
payment_api = PaymentAPI()

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    is_admin = message.from_user.id in ADMIN_IDS
    keyboard = get_admin_kb() if is_admin else get_user_kb()
    await message.answer(
        "🌟 Добро пожаловать в ZelenkaCheck!\n\n"
        "🤖 Я помогу проверить профили пользователей Zelenka.guru\n"
        "📌 Выберите нужное действие в меню:",
        reply_markup=keyboard
    )

@dp.message_handler(text="🔍 Проверить профиль")
async def request_profile(message: types.Message):
    await ProfileCheck.waiting_for_id.set()
    await message.answer(
        "🎯 Введите ID пользователя или ссылку на профиль\n\n"
        "📝 Поддерживаемые форматы:\n"
        "• ID пользователя\n"
        "• lolz.live/members/ID\n"
        "• zelenka.guru/members/ID\n"
        "• lzt.market/members/ID",
        reply_markup=get_back_kb()
    )

@dp.message_handler(text="💡 Помощь")
async def help_cmd(message: types.Message):
    await message.answer(
        "📚 Инструкция по использованию:\n\n"
        "1️⃣ Перейдите сюда https://lolz.live/account/personal-details и скопируйте свой ID (Постоянная ссылка на профиль)\n"
        "2️⃣ Нажмите '🔍 Проверить профиль'\n"
        "3️⃣ Вставьте ссылку или ID пользователя\n"
        "4️⃣ Получите подробный отчет\n\n"
        "🔧 Дополнительные функции доступны в меню"
    )

@dp.message_handler(text="ℹ️ О боте")
async def about_cmd(message: types.Message):
    await message.answer(
        "🤖 ZelenkaCheck Bot\n\n"
        "✨ Возможности:\n"
        "• Проверка статуса профиля\n"
        "• Анализ закрепленного поста\n"
        "• Мониторинг изменений\n\n"
        "🎯 Создан для удобной проверки рекламных профилей"
    )


@dp.message_handler(text="💰 Управление выплатами")
async def payment_management(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    applications = await db.get_pending_applications()
    if not applications:
        await message.answer("📝 Нет ожидающих выплат")
        return

    text = "📋 Список заявок на выплату:\n\n"
    for app in applications:
        text += f"👤 ID форума: {app[2]}\n📅 Дата: {app[4]}\n\n"

    await message.answer(
        text,
        reply_markup=get_admin_payments_kb(applications)
    )

@dp.message_handler(text="⚙️ Настройки")
async def settings_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⚠️ Нет доступа!")
        return

    settings = settings_manager.load_settings()
    current_mode = settings.get('check_mode', 'exact')
    mode_text = "Точная проверка" if current_mode == "exact" else "Только URL"

    await message.answer(
        f"⚙️ Настройки проверки профилей\n\n"
        f"Текущий режим: {mode_text}",
        reply_markup=get_settings_kb(current_mode)
    )

@dp.callback_query_handler(lambda c: c.data == "toggle_check_mode")
async def toggle_check_mode(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("⚠️ Нет доступа!", show_alert=True)
        return

    settings = settings_manager.load_settings()
    current_mode = settings.get('check_mode', 'exact')
    new_mode = 'url' if current_mode == 'exact' else 'exact'

    settings['check_mode'] = new_mode
    settings_manager.save_settings(settings)

    mode_text = "Точная проверка" if new_mode == "exact" else "Только URL"
    await callback_query.message.edit_text(
        f"⚙️ Настройки проверки профилей\n\n"
        f"Текущий режим: {mode_text}",
        reply_markup=get_settings_kb(new_mode)
    )

@dp.callback_query_handler(lambda c: c.data == "recheck")
async def recheck_profile(callback_query: types.CallbackQuery):
    await callback_query.answer("🔄 Запущена повторная проверка")

@dp.message_handler(text="🔄 Перезагрузить шаблоны")
async def reload_templates(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    settings_manager.reload_templates()
    await message.answer("✅ Шаблоны успешно перезагружены!")


@dp.callback_query_handler(lambda c: c.data == "approve_payment")
async def set_payment_amount(callback: types.CallbackQuery, state: FSMContext):
    message_text = callback.message.text
    try:
        # More robust ID extraction
        forum_id = message_text.split('ID форума: ')[1].split('\n')[0].strip()

        async with state.proxy() as data:
            data['forum_id'] = forum_id

        await PaymentStates.waiting_for_amount.set()
        await callback.message.answer(f"💰 Введите сумму выплаты в рублях для ID {forum_id}:")
    except IndexError:
        await callback.message.answer("⚠️ Не удалось определить ID пользователя. Попробуйте снова.")


@dp.message_handler(state=ProfileCheck.waiting_for_id)
async def process_id(message: types.Message, state: FSMContext):
    user_id = extract_user_id(message.text)
    if not user_id:
        await message.answer(
            "❌ Неверный формат ссылки или ID\n\n"
            "📝 Примеры правильных форматов:\n"
            "• 5680221\n"
            "• lolz.live/members/5680221\n"
            "• zelenka.guru/members/5680221",
            reply_markup=get_profile_check_kb()
        )
        return

    settings = settings_manager.load_settings()
    check_mode = settings.get('check_mode', 'exact')
    template = settings_manager.load_template()

    await message.answer("🔄 Получаем данные профиля...")
    data = await api.get_profile_data(user_id)

    if not data or not data.get('profile_posts'):
        await message.answer(
            "❌ Профиль не найден или недоступен",
            reply_markup=get_profile_check_kb()
        )
        await state.finish()
        return

    post = data['profile_posts'][0]
    timeline_user = post.get('timeline_user', {})
    status = timeline_user.get('custom_title', '')
    pinned_post = post.get('post_body', '')

    # Get avatar URL
    avatar_url = timeline_user.get('links', {}).get('avatar', 'Аватар не найден')

    status_match = "✅" if check_status(status, template['custom_title'], check_mode) else "❌"
    pinned_match = "✅" if check_pinned_post(pinned_post, template['pinned_post']) else "❌"

    result = (
        f"📊 Результаты проверки:\n\n"
        f"👤 Пользователь: {timeline_user.get('username')}\n"
        f"🆔 ID: {user_id}\n\n"
        f"📌 Статус: {status_match}\n"
        f"📝 Закреп: {pinned_match}\n"
        f"🖼 Аватар: {avatar_url}"
    )

    if status_match == "❌" or pinned_match == "❌":
        await message.answer(result, reply_markup=get_profile_check_kb())
    else:
        await message.answer(result, reply_markup=get_payment_request_kb())

    await state.finish()


@dp.message_handler(state=PaymentStates.waiting_for_amount)
async def process_payment_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        async with state.proxy() as data:
            forum_id = data['forum_id']

        # Get user_id from database
        user_id = await db.get_user_id_by_forum_id(forum_id)

        if await db.check_payment_exists(forum_id):
            await message.answer(f"⚠️ Выплата для ID {forum_id} уже была произведена!")
            await state.finish()
            return

        payment_result = await payment_api.send_payment(forum_id, amount)
        if payment_result:
            await db.update_application_status(forum_id, 'approved')
            await message.answer(f"✅ Выплата {amount}₽ для ID {forum_id} отправлена с холдом")
            # Notify user
            if user_id:
                await bot.send_message(user_id, f"✅ Ваша заявка одобрена! Выплата {amount}₽ отправлена с холдом")
        else:
            await message.answer("❌ Ошибка при отправке выплаты")
    except ValueError:
        await message.answer("❌ Введите корректную сумму")
    finally:
        await state.finish()


@dp.callback_query_handler(lambda c: c.data == "reject_payment")
async def reject_payment(callback: types.CallbackQuery):
    try:
        forum_id = callback.message.text.split('ID форума: ')[1].split('\n')[0].strip()
        # Get user_id from database
        user_id = await db.get_user_id_by_forum_id(forum_id)

        await db.update_application_status(forum_id, 'rejected')
        await callback.message.answer(f"❌ Выплата для ID {forum_id} отклонена")
        # Notify user
        if user_id:
            await bot.send_message(user_id, "❌ Ваша заявка на выплату отклонена")
    except (IndexError, ValueError):
        await callback.message.answer("⚠️ Ошибка при отклонении выплаты")


@dp.callback_query_handler(lambda c: c.data == "submit_payment_request")
async def submit_payment_request(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"
    forum_id = callback.message.text.split('🆔 ID: ')[1].split('\n')[0]
    avatar_url = callback.message.text.split('🖼 Аватар: ')[1].split('\n')[0]

    await db.add_application(user_id, forum_id, "parameters")

    admin_message = (
        f"🆕 Новая заявка на выплату!\n\n"
        f"👤 От пользователя: @{username}\n"
        f"🆔 ID форума: {forum_id}\n"
        f"📊 Статус проверки: ✅ Все параметры совпадают\n"
        f"🖼 Аватар: {avatar_url}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                admin_message,
                reply_markup=get_payment_management_kb()
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")



@dp.message_handler(commands=['payments'], user_id=ADMIN_IDS)
async def show_pending_payments(message: types.Message):
    applications = await db.get_pending_applications()
    if not applications:
        await message.answer("Нет ожидающих выплат")
        return

    await message.answer(
        "Список ожидающих выплат:",
        reply_markup=get_admin_payments_kb(applications)
    )

@dp.callback_query_handler(lambda c: c.data.startswith('approve_payment_'), user_id=ADMIN_IDS)
async def approve_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split('_')[2])

    payment_result = await payment_api.send_payment(user_id, 1)
    if payment_result and payment_result.get('success'):
        await db.update_application_status(user_id, 'approved')
        await callback.message.answer(f"✅ Выплата для ID {user_id} одобрена и отправлена")
    else:
        await callback.message.answer(f"❌ Ошибка при отправке выплаты для ID {user_id}")

@dp.callback_query_handler(lambda c: c.data == "back_to_main", state="*")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    is_admin = callback.from_user.id in ADMIN_IDS
    keyboard = get_admin_kb() if is_admin else get_user_kb()

    await callback.message.answer(
        "🌟 Главное меню",
        reply_markup=keyboard
    )
    await callback.message.delete()

async def on_startup(dp):
    await db.init()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)