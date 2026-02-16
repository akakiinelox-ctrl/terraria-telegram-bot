from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

SEEDS = {
    "drunk": {
        "name": "🍷 Пьяный мир (Drunk World)",
        "code": "05162020",
        "desc": "Сразу оба зла (Искажение и Багрянец). Луна в виде улыбки, музыка из Terraria Otherworld. Идеально для тех, кто хочет всё и сразу."
    },
    "bees": {
        "name": "🐝 Пчелиный мир (Not the bees)",
        "code": "not the bees",
        "desc": "Мир, где почти всё — это джунгли, соты и мёд. Пчелы повсюду, даже из блоков. Самый 'липкий' сид."
    },
    "zenith": {
        "name": "🌌 Зенит (Get fixed boi)",
        "code": "get fixed boi",
        "desc": "Ультимативный сид. Смесь всех секретных миров. Начинаешь в аду, небо — это грибной биом, а боссы имеют новые безумные атаки."
    },
    "constant": {
        "name": "👁 Не голодай (The Constant)",
        "code": "constant",
        "desc": "Кроссовер с Don't Starve. Система голода (нужно есть), темнота наносит урон, и наложен специальный 'старый' фильтр изображения."
    },
    "trap": {
        "name": "🧨 Мир ловушек (No traps)",
        "code": "no traps",
        "desc": "Ловушки везде. Нажимные плиты повсюду: под землей, на поверхности, в сундуках. Будь очень осторожен."
    }
}

@router.callback_query(F.data == "m_seeds")
async def seeds_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for key, val in SEEDS.items():
        builder.row(types.InlineKeyboardButton(text=val['name'], callback_data=f"seed_v:{key}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main"))
    
    await callback.message.edit_text(
        "🌍 <b>Секретные сиды миров</b>\n\nРазработчики спрятали особые режимы игры за кодами генерации. Выбери сид, чтобы узнать детали:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("seed_v:"))
async def seed_view(callback: types.CallbackQuery):
    key = callback.data.split(":")[1]
    seed = SEEDS[key]
    text = (f"🌍 <b>{seed['name']}</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"🔑 <b>Код генерации:</b> <code>{seed['code']}</code>\n\n"
            f"📝 <b>Что изменится:</b>\n{seed['desc']}")
    
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="m_seeds"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
