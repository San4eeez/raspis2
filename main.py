import requests
from bs4 import BeautifulSoup


def fetch_schedule(url):
    response = requests.get(url)
    response.raise_for_status()  # Проверяем, что запрос успешен

    soup = BeautifulSoup(response.text, 'html.parser')
    schedule = []

    schedule_cards = soup.find_all('div', class_='card h-100')
    for card in schedule_cards:
        day_header = card.find('h5', class_='card-title')
        if day_header:
            day_info = day_header.get_text(strip=True)
            day_parts = day_info.split(' - ')
            weekday, date = day_parts if len(day_parts) == 2 else ("", "")

        table = card.find('table', class_='table table-hover table-striped gs-5')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 4:
                    # lesson_number_and_time = columns[0].text.strip()
                    # lesson_number = "".join(filter(str.isdigit, lesson_number_and_time))
                    time_tag = columns[0].find('p')
                    time = time_tag.text.strip() if time_tag else ""

                    subject_data = columns[1].get_text(" ", strip=True).replace("РТК", "").strip()
                    room = columns[2].get_text(strip=True)
                    teacher = columns[3].get_text(strip=True)

                    if subject_data:
                        schedule.append({
                            'День недели': weekday,
                            'Дата': date,
                            # 'Урок': lesson_number,
                            'Время': time,
                            'Предмет': subject_data,
                            'Кабинет': room,
                            'Преподаватель': teacher
                        })

    return schedule


url = "https://e-spo.ru/org/rasp/export/site/index?date=2025-03-17&pid=1&RaspBaseSearch%5Bgroup_id%5D=44&RaspBaseSearch%5Bsemestr%5D=vesna&RaspBaseSearch%5Bprepod_id%5D="
schedule = fetch_schedule(url)

for lesson in schedule:
    print(lesson)
