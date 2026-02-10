import os
import json
import logging
import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN") or "ТВОЙ_ТОКЕН_ЗДЕСЬ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ЗАГРУЗКА ДАННЫХ ---
def get_data(filename):
    try:
        with open(f'data/{filename}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки {filename}: {e}")
        return {}

# ==========================================
# 🏠 ГЛАВНОЕ МЕНЮ
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👾 Боссы", callback_data="m_bosses"),
                types.InlineKeyboardButton(text="⚔️ События", callback_data="m_events"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Классы", callback_data="m_classes"),
                types.InlineKeyboardButton(text="👥 NPC", callback_data="m_npcs"))
    builder.row(types.InlineKeyboardButton(text="🎲 Мне скучно", callback_data="m_random"))
    
    await message.answer(
        "🛠 **Terraria Tactical Assistant**\n\nПривет, Террариец! Я помогу тебе подготовиться к любой угрозе. Выбери раздел:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    await cmd_start(callback.message)

# ==========================================
# ⚔️ РАЗДЕЛ: СОБЫТИЯ (ТАКТИЧЕСКИЙ ВИД)
# ==========================================
@dp.callback_query(F.data == "m_events")
async def events_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="ev_l:pre_hm"),
                types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="ev_l:hm"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Меню", callback_data="to_main"))
    await callback.message.edit_text("📅 **Выберите этап для просмотра нашествий:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ev_l:"))
async def events_list(callback: types.CallbackQuery):
    stage = callback.data.split(":")[1]
    data = get_data('events')[stage]
    builder = InlineKeyboardBuilder()
    for key, ev in data.items():
        builder.row(types.InlineKeyboardButton(text=ev['name'], callback_data=f"ev_i:{stage}:{key}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_events"))
    await callback.message.edit_text("🌊 **Выберите событие для тактического разбора:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ev_i:"))
async def event_info(callback: types.CallbackQuery):
    _, stage, key = callback.data.split(":")
    ev = get_data('events')[stage][key]
    
    text = (
        f"⚔️ **{ev['name']}**\n"
        f"━━━━━━━━━━━━━━\n"
        f"🔥 **Сложность:** {ev.get('difficulty', '???')}\n"
        f"💰 **Профит:** {ev.get('profit', '???')}\n\n"
        f"📢 **Триггер:** {ev['trigger']}\n"
        f"🌊 **Волны:** {ev['waves']}\n"
        f"🎁 **Дроп:** {ev['drops']}\n\n"
        f"🛠 **ТАКТИКА:** \n_{ev.get('arena_tip', 'Стандартная арена.')}_"
    )
    
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"ev_l:{stage}"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# ==========================================
# 👾 РАЗДЕЛ: БОССЫ
# ==========================================
@dp.callback_query(F.data == "m_bosses")
async def bosses_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🟢 До-Хардмод", callback_data="b_l:pre_hm"),
                types.InlineKeyboardButton(text="🔴 Хардмод", callback_data="b_l:hm"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Меню", callback_data="to_main"))
    await callback.message.edit_text("👹 **Выберите категорию боссов:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_l:"))
async def bosses_list(callback: types.CallbackQuery):
    st = callback.data.split(":")[1]
    data = get_data('bosses')[st]
    builder = InlineKeyboardBuilder()
    for k, v in data.items():
        builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"b_s:{st}:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_bosses"))
    await callback.message.edit_text("🎯 **Выберите цель:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_s:"))
async def boss_selected(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    boss = get_data('bosses')[st][k]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Экипировка", callback_data=f"b_g:{st}:{k}"),
                types.InlineKeyboardButton(text="🎁 Дроп", callback_data=f"b_f:{st}:{k}:drops"))
    builder.row(types.InlineKeyboardButton(text="⚔️ Тактика", callback_data=f"b_f:{st}:{k}:tactics"),
                types.InlineKeyboardButton(text="🏟️ Арена", callback_data=f"b_f:{st}:{k}:arena"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_l:{st}"))
    await callback.message.edit_text(f"📖 **{boss['name']}**\n\n{boss['general']}", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_f:"))
async def boss_field_info(callback: types.CallbackQuery):
    _, st, k, fld = callback.data.split(":")
    txt = get_data('bosses')[st][k].get(fld, "Данные обновляются...")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{st}:{k}"))
    await callback.message.edit_text(f"📝 **Информация:**\n\n{txt}", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_g:"))
async def boss_gear_menu(callback: types.CallbackQuery):
    _, st, k = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    clss = {"warrior": "⚔️ Воин", "ranger": "🎯 Стрелок", "mage": "🔮 Маг", "summoner": "🐍 Призыв"}
    for cid, name in clss.items():
        builder.row(types.InlineKeyboardButton(text=name, callback_data=f"b_gc:{st}:{k}:{cid}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_s:{st}:{k}"))
    await callback.message.edit_text("🛡️ **Выберите свой класс:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_gc:"))
async def boss_gear_final(callback: types.CallbackQuery):
    _, st, k, cid = callback.data.split(":")
    items = get_data('bosses')[st][k]['classes'][cid]
    builder = InlineKeyboardBuilder()
    for i, item in enumerate(items):
        builder.row(types.InlineKeyboardButton(text=item['name'], callback_data=f"b_gi:{st}:{k}:{cid}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"b_g:{st}:{k}"))
    await callback.message.edit_text("🎒 **Лучшие предметы для этого боя:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("b_gi:"))
async def boss_gear_alert(callback: types.CallbackQuery):
    _, st, k, cid, i = callback.data.split(":")
    item = get_data('bosses')[st][k]['classes'][cid][int(i)]
    await callback.answer(f"🛠 {item['name']}\n{item['craft']}", show_alert=True)

# ==========================================
# 🛡️ РАЗДЕЛ: КЛАССЫ
# ==========================================
@dp.callback_query(F.data == "m_classes")
async def classes_menu(callback: types.CallbackQuery):
    data = get_data('classes')
    builder = InlineKeyboardBuilder()
    for k, v in data.items():
        builder.row(types.InlineKeyboardButton(text=v['name'], callback_data=f"cl_s:{k}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text("🛡️ **Выберите класс для изучения билда:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_s:"))
async def class_stages(callback: types.CallbackQuery):
    cid = callback.data.split(":")[1]
    builder = InlineKeyboardBuilder()
    sts = {"start": "🟢 Старт", "pre_hm": "🟡 До ХМ", "hm_start": "🔴 Ранний ХМ", "endgame": "🟣 Финал"}
    for k, v in sts.items():
        builder.add(types.InlineKeyboardButton(text=v, callback_data=f"cl_c:{cid}:{k}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_classes"))
    await callback.message.edit_text("📅 **Выберите этап прохождения:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_c:"))
async def class_cats(callback: types.CallbackQuery):
    _, cid, sid = callback.data.split(":")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛡️ Броня", callback_data=f"cl_i:{cid}:{sid}:armor"),
                types.InlineKeyboardButton(text="⚔️ Оружие", callback_data=f"cl_i:{cid}:{sid}:weapons"))
    builder.row(types.InlineKeyboardButton(text="💍 Аксессуары", callback_data=f"cl_i:{cid}:{sid}:accessories"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_s:{cid}"))
    await callback.message.edit_text("Что будем смотреть?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_i:"))
async def class_items_list(callback: types.CallbackQuery):
    _, cid, sid, cat = callback.data.split(":")
    data = get_data('classes')[cid]['stages'][sid][cat]
    builder = InlineKeyboardBuilder()
    for i, itm in enumerate(data):
        builder.row(types.InlineKeyboardButton(text=itm['name'], callback_data=f"cl_inf:{cid}:{sid}:{cat}:{i}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cl_c:{cid}:{sid}"))
    await callback.message.edit_text("🎒 **Выбери предмет для инфо:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cl_inf:"))
async def class_item_alert(callback: types.CallbackQuery):
    _, cid, sid, cat, i = callback.data.split(":")
    itm = get_data('classes')[cid]['stages'][sid][cat][int(i)]
    await callback.answer(f"🛠 {itm['name']}\n{itm['info']}", show_alert=True)

# ==========================================
# 👥 РАЗДЕЛ: NPC
# ==========================================
@dp.callback_query(F.data == "m_npcs")
async def npc_main(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📜 Список жителей", callback_data="n_list"),
                types.InlineKeyboardButton(text="🏡 Советы по домам", callback_data="n_tips"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text("👥 **Справочник NPC**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "n_list")
async def npc_list_all(callback: types.CallbackQuery):
    npcs = get_data('npcs')['npcs']
    builder = InlineKeyboardBuilder()
    for n in npcs:
        builder.add(types.InlineKeyboardButton(text=n['name'], callback_data=f"n_i:{n['name']}"))
    builder.adjust(2).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_npcs"))
    await callback.message.edit_text("👤 **Выберите NPC:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("n_i:"))
async def npc_detail(callback: types.CallbackQuery):
    name = callback.data.split(":")[1]
    npc = next(n for n in get_data('npcs')['npcs'] if n['name'] == name)
    txt = f"👤 **{npc['name']}**\n📍 Биом: {npc['biome']}\n❤️ Любит: {npc['loves']}\n😊 Нравится: {npc['likes']}"
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="n_list"))
    await callback.message.edit_text(txt, reply_markup=builder.as_markup())

# ==========================================
# 🎲 РАНДОМАЙЗЕР
# ==========================================
@dp.callback_query(F.data == "m_random")
async def random_challenge(callback: types.CallbackQuery):
    chals = [
        "🏹 **Стрелок-Робингуд:** Только луки. Никакого огнестрела!",
        "⚔️ **Истинный Рыцарь:** Только мечи без снарядов (True Melee).",
        "🎣 **Рыбак-Воин:** Можно использовать только снаряжение из рыбалки.",
        "💣 **Подрывник:** Убивай боссов только взрывчаткой (бомбы, динамит).",
        "🌵 **Друид:** Используй только снаряжение, связанное с растениями.",
        "🧙 **Гарри Поттер:** Только магические жезлы. Без книг."
    ]
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🎲 Еще раз", callback_data="m_random"),
                                          types.InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main"))
    await callback.message.edit_text(f"🎲 **Твой челлендж:**\n\n{random.choice(chals)}", reply_markup=builder.as_markup())

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
