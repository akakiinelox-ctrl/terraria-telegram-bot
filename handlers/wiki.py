        # 4. Собираем текст (Улучшенный поиск)
        content = soup.find('div', class_='mw-parser-output')
        description = ""
        
        if content:
            # Сначала удаляем элементы, которые точно НЕ являются текстом описания
            for junk in content.find_all(['table', 'aside', 'script', 'style', 'div']):
                # Проверяем, не является ли div частью текста (иногда бывает)
                if not (junk.get('class') and 'mw-empty-elt' in junk.get('class')):
                    junk.decompose()

            # МЕТОД 1: Пробуем собрать абзацы
            paragraphs = content.find_all('p')
            for p in paragraphs:
                txt = clean_text(p.text)
                if len(txt) > 30:
                    description += txt + "\n\n"
                if len(description) > 800:
                    break
            
            # МЕТОД 2: Если абзацы пустые, берем весь текст блока (План Б)
            if len(description.strip()) < 10:
                raw_text = content.get_text(separator="\n")
                # Чистим от пустых строк и лишних пробелов
                lines = [clean_text(line) for line in raw_text.split('\n') if len(clean_text(line)) > 40]
                description = "\n\n".join(lines[:3]) # Берем первые 3 содержательные строки

        if not description or len(description.strip()) < 10:
            description = "Описание предмета слишком сложное для краткого вывода. Попробуйте найти его по категории или уточнить запрос."

