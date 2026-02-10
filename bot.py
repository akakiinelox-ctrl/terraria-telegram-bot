import os
import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

# Укажи свой токен напрямую или через переменные окружения
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_ЗДЕСЬ"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ЗАГРУЗКА ДАННЫХ ---
def load_boss_data():
    try:
        with open('data/bosses.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка JSON Боссов: {e}")
        return None

def load_npc_data():
    try:
        with open('data/npcs.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка JSON NPC: {e}")
        return None

# --- ГЛАВНОЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="main_bosses"))
    builder.row(types.InlineKeyboardButton(text="👥 NPC и Счастье", callback_data="main_npcs"))
    
    await message.answer(
        "👋 Привет! Я твой справочник по Terraria.\nВыбери нужный раздел ниже:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "to_main")
async def back_to_main_callback(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="main_bosses"))
    builder.row(types.InlineKeyboardButton(text="👥 NPC и Счастье", callback_data="main_npcs"))
    await callback.message.edit_text("Главное меню:", reply_markup=builder.as_markup())

# --- БЛОК БОССОВ ---
@dp.callback_query(F.data == "main_bosses")
async def bosses_main_select(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="list:pre_hm"))
    builder.row(types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="list:hm"))
    builder.row(types.InlineKeyboardButton(text="⬅️ В главное меню", callback_data="to_main"))
    await callback.message.edit_text("👹 Выбери этап игры:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("list:"))
async def show_boss_list(callback: types.CallbackQuery):
    stage = callback.data.split(":")[1]
    data = load_boss_data()
    builder = InlineKeyboardBuilder()
    for key, boss in data[stage].items():
        builder.row(types.InlineKeyboardButton(text=boss['name'], callback_data=f"select:{stage}:{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_bosses"))
    await callback.message.edit_text("👹 Выбери босса:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("select:"))
async def boss_main_menu(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    data = load_boss_data()
    boss = data[stage][key]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Экип", callback_data=f"gear_menu:{stage}:{key}"))
    builder.row(
        types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"info:{stage}:{key}:tactics"),
        types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"info:{stage}:{key}:arena")
    )
    builder.row(types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"info:{stage}:{key}:drops"))
    builder.row(types.InlineKeyboardButton(text="⬅️ К списку", callback_data=f"list:{stage}"))
    await callback.message.edit_text(f"📖 **Гайд: {boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup(), parse_mode="Markdown")

# (Вспомогательные функции для экипировки и крафта оставляем такими же, как в твоем коде)
@dp.callback_query(F.data.startswith("gear_menu:"))
async def gear_classes_menu(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⚔️ Воин", callback_data=f"class_gear:{stage}:{key}:warrior"),
                types.InlineKeyboardButton(text="🎯 Стрелок", callback_data=f"class_gear:{stage}:{key}:ranger"))
    builder.row(types.InlineKeyboardButton(text="🔮 Маг", callback_data=f"class_gear:{stage}:{key}:mage"),
                types.InlineKeyboardButton(text="🐍 Призыв", callback_data=f"class_gear:{stage}:{key}:summoner"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select:{stage}:{key}"))
    await callback.message.edit_text("🛡️ **Выбери класс:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("class_gear:"))
async def show_items_as_buttons(callback: types.CallbackQuery):
    _, stage, key, class_id = callback.data.split(":")
    data = load_boss_data()
    items = data[stage][key]['classes'][class_id]
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.row(types.InlineKeyboardButton(text=item['name'], callback_data=f"item_craft:{stage}:{key}:{class_id}:{items.index(item)}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"gear_menu:{stage}:{key}"))
    await callback.message.edit_text(f"🎒 **Снаряжение ({class_id}):**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("item_craft:"))
async def show_craft_alert(callback: types.CallbackQuery):
    _, stage, key, class_id, item_index = callback.data.split(":")
    data = load_boss_data()
    item = data[stage][key]['classes'][class_id][int(item_index)]
    await callback.answer(f"🛠 {item['name']}:\n{item['craft']}", show_alert=True)

@dp.callback_query(F.data.startswith("info:"))
async def show_other_info(callback: types.CallbackQuery):
    _, stage, key, field = callback.data.split(":")
    data = load_boss_data()
    boss = data[stage][key]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select:{stage}:{key}"))
    await callback.message.edit_text(f"📝 **{field.capitalize()}:**\n\n{boss[field]}", reply_markup=builder.as_markup())

# --- БЛОК NPC ---
@dp.callback_query(F.data == "main_npcs")
async def npc_main_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📜 Список всех NPC", callback_data="npc_list"))
    builder.row(types.InlineKeyboardButton(text="📊 Таблица цен", callback_data="npc_prices"))
    builder.row(types.InlineKeyboardButton(text="🏡 Советы по расселению", callback_data="npc_tips"))
    builder.row(types.InlineKeyboardButton(text="⬅️ В главное меню", callback_data="to_main"))
    await callback.message.edit_text("👥 **Справочник жителей**\nЗдесь ты узнаешь, как сделать NPC счастливыми.", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "npc_prices")
async def npc_prices_table(callback: types.CallbackQuery):
    table = (
        "📊 **Влияние счастья на цены:**\n\n"
        "• **❤️ Восторг (75%):** Самая низкая цена. Продаёт Пилон.\n"
        "• **😊 Доволен (88%):** Скидка есть. Продаёт Пилон.\n"
        "• **😐 Нейтрально (100%):** Обычная цена.\n"
        "• **☹️ Недоволен (112%):** Наценка.\n"
        "• **😡 Ярость (150%):** Максимальная цена."
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_npcs"))
    await callback.message.edit_text(table, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "npc_tips")
async def npc_tips_info(callback: types.CallbackQuery):
    tips = (
        "🏡 **Лучшие связки для Пилонов:**\n\n"
        "🌵 **Пустыня:** Оружейник + Медсестра\n"
        "❄️ **Снега:** Механик + Гоблин (огромная скидка!)\n"
        "🌳 **Лес:** Гид + Зоолог\n"
        "🌿 **Джунгли:** Дриада + Знахарь\n"
        "🍄 **Грибы:** Трюфель + Гид\n\n"
        "⚠️ *Не более 3-х NPC рядом, иначе они станут несчастными.*"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_npcs"))
    await callback.message.edit_text(tips, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "npc_list")
async def show_npc_names(callback: types.CallbackQuery):
    data = load_npc_data()
    builder = InlineKeyboardBuilder()
    for npc in data['npcs']:
        builder.add(types.InlineKeyboardButton(text=npc['name'], callback_data=f"npc_info:{npc['name']}"))
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_npcs"))
    await callback.message.edit_text("👤 Выбери жителя для подробностей:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("npc_info:"))
async def show_single_npc(callback: types.CallbackQuery):
    name = callback.data.split(":")[1]
    data = load_npc_data()
    npc = next((item for item in data['npcs'] if item['name'] == name), None)
    
    info = (
        f"{npc['name']}\n"
        f"📍 **Биом:** {npc['biome']}\n"
        f"📦 **Бонус:** {npc['bonus']}\n"
        f"✅ **Прибытие:** {npc['arrival']}\n\n"
        f"❤️ **Любит:** {npc['loves']}\n"
        f"😊 **Нравится:** {npc['likes']}\n"
        f"☹️ **Не любит:** {npc['dislikes']}\n"
        f"😡 **Ненавидит:** {npc['hates']}"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="npc_list"))
    await callback.message.edit_text(info, reply_markup=builder.as_markup())

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
