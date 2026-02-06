import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


BOSSES = load_json("data/bosses.json")
PROGRESSION = load_json("data/progression.json")


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🎮 *Terraria Guide Bot*\n\n"
        "Команды:\n"
        "/boss <имя> — подробный гайд\n"
        "/prepare <имя> — подготовка\n"
        "/next — кого бить дальше",
        parse_mode="Markdown"
    )


@dp.message_handler(commands=["boss"])
async def boss(message: types.Message):
    args = message.get_args().lower().strip()

    if not args:
        await message.answer(
            "🧿 Боссы:\n" +
            "\n".join(f"• {b['ru']}" for b in BOSSES.values())
        )
        return

    matches = [k for k in BOSSES if args in k]
    if not matches:
        await message.answer("❌ Босс не найден")
        return

    b = BOSSES[matches[0]]

    await message.answer(
        f"👁 *{b['ru']}*\n"
        f"🗺 Этап: {b['этап']}\n\n"
        f"📌 Когда идти:\n{b['когда']}\n\n"
        f"🏗 Арена:\n{b['арена']}\n\n"
        f"⚔️ Фазы:\n" +
        "\n".join(f"• {p}" for p in b['фазы']) +
        "\n\n❌ Ошибки:\n" +
        "\n".join(f"• {e}" for e in b['ошибки']) +
        "\n\n🎁 Зачем убивать:\n" +
        b['зачем'],
        parse_mode="Markdown"
    )


@dp.message_handler(commands=["prepare"])
async def prepare(message: types.Message):
    args = message.get_args().lower().strip()
    matches = [k for k in BOSSES if args in k]

    if not matches:
        await message.answer("❌ Укажи босса")
        return

    b = BOSSES[matches[0]]

    await message.answer(
        f"🧰 *Подготовка к бою: {b['ru']}*\n\n" +
        "\n".join(f"• {p}" for p in b['подготовка']),
        parse_mode="Markdown"
    )


@dp.message_handler(commands=["next"])
async def next_boss(message: types.Message):
    chain = PROGRESSION.get("Дохардмод", [])
    await message.answer(
        "🎯 Рекомендуемый порядок боссов:\n" +
        "\n".join(f"{i+1}. {name}" for i, name in enumerate(chain))
    )


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)