import html # Добавь этот импорт в самое начало файла

# ==========================================
# 🧠 МОЗГ: СВОБОДНЫЙ ЭКСПЕРТ (Исправленная версия)
# ==========================================

async def ask_guide_ai(message_to_edit: types.Message, query: str):
    if not client:
        await message_to_edit.edit_text("❌ Ошибка: Нет API ключа Groq.")
        return

    system_prompt = (
        "Ты — Гид из игры Terraria. Ты — эксперт, знающий всё о версии 1.4.4. "
        "Твоя цель: помогать игрокам. Отвечай подробно и структурировано. "
        "\n\nВАЖНО: Используй ТОЛЬКО HTML теги для оформления (<b>болд</b>, <i>курсив</i>, <code>код</code>). "
        "Никаких символов Markdown (* или _). "
        "\n1. Если спрашивают порядок боссов — дай четкий список. "
        "\n2. Если спрашивают крафт — укажи ингредиенты и рабочее место. "
        "\n3. Общайся дружелюбно, как персонаж Гид."
    )

    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            model="llama-3.3-70b-versatile", 
            temperature=0.5, 
        )
        
        response = chat_completion.choices[0].message.content
        
        # Кнопки под ответом
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🤔 Спросить что-то ещё", callback_data="m_search"))
        builder.row(types.InlineKeyboardButton(text="🏠 В меню", callback_data="to_main"))
        
        # Используем parse_mode="HTML" вместо Markdown
        await message_to_edit.edit_text(
            response, 
            reply_markup=builder.as_markup(), 
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"🔴 ОШИБКА AI: {e}") 
        # В случае ошибки просто отправляем текст без разметки, чтобы точно дошло
        await message_to_edit.edit_text(f"🤯 Гид: Прости, путник, мысли спутались. Попробуй еще раз.\n(Тех. инфо: {str(e)[:50]})")

# --- ОБРАБОТЧИКИ ЧАТА ---

@dp.callback_query(F.data == "m_search")
async def chat_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.wait_item_name)
    # Здесь тоже меняем на HTML стиль
    await callback.message.answer(
        "👋 <b>Я слушаю, Террариец!</b>\n\n"
        "Спрашивай о чём угодно:\n"
        "▫️ <i>Как скрафтить Зенит?</i>\n"
        "▫️ <i>Броня на мага перед Плантерой?</i>\n"
        "▫️ <i>Кто идет после Пчелы?</i>",
        parse_mode="HTML"
    )
    await callback.answer()
