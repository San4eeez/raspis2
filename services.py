import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
from models import GROUPS, TEACHERS


def parse_lesson_number_and_time(lesson_number_and_time: str) -> str:
    """Разделяет номер урока и время."""
    if lesson_number_and_time:
        if len(lesson_number_and_time) >= 2 and lesson_number_and_time[1] == '0':
            # Если второй символ 0
            lesson_number = lesson_number_and_time[:2]
            time = lesson_number_and_time[2:]
        else:
            # Если второй символ не 0
            lesson_number = lesson_number_and_time[:1]
            time = lesson_number_and_time[1:]
        return f"{lesson_number} {time}"  # Добавляем пробел
    return lesson_number_and_time


def fetch_schedule(entity_id: int, entity_type: str = "group", target_date: Optional[str] = None) -> List[str]:
    """Получает расписание для указанной группы или преподавателя."""
    if entity_type == "group":
        url = f"https://e-spo.ru/org/rasp/export/site/index?pid=1&RaspBaseSearch%5Bgroup_id%5D={entity_id}&RaspBaseSearch%5Bsemestr%5D=vesna&RaspBaseSearch%5Bprepod_id%5D="
    else:
        url = f"https://e-spo.ru/org/rasp/export/site/index?pid=1&RaspBaseSearch%5Bgroup_id%5D=&RaspBaseSearch%5Bsemestr%5D=vesna&RaspBaseSearch%5Bprepod_id%5D={entity_id}"

    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    schedule = []

    schedule_cards = soup.find_all('div', class_='card h-100')
    for card in schedule_cards:
        day_header = card.find('h5', class_='card-title')
        if day_header:
            day_info = day_header.get_text(strip=True)
            day_parts = day_info.split(' - ')
            weekday, date = day_parts if len(day_parts) == 2 else ("", "")

            if target_date and target_date != date:
                continue

        table = card.find('table', class_='table table-hover table-striped gs-5')
        if table:
            rows = table.find_all('tr')
            lessons = []
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 4:
                    lesson_number_and_time = parse_lesson_number_and_time(columns[0].text.strip())
                    subject_data = columns[1].get_text(" ", strip=True).replace("РТК", "").strip()
                    room = columns[2].get_text(strip=True)
                    teacher_or_group = columns[3].get_text(strip=True)

                    if subject_data:
                        if entity_type == "group":
                            lessons.append(
                                f"Урок {lesson_number_and_time}\nПредмет: {subject_data}\nКабинет: {room}\nПреподаватель: {teacher_or_group}\n")
                        else:
                            lessons.append(
                                f"Урок {lesson_number_and_time}\nПредмет: {subject_data}\nКабинет: {room}\nГруппа: {teacher_or_group}\n")

            if lessons:
                schedule.append(f"{weekday}, {date}\n" + "\n".join(lessons))

    return schedule