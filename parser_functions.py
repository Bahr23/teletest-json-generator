import json

import requests
from bs4 import BeautifulSoup


def get_questions(soap):
    questions = []
    questions_raw = soap.find(attrs={"class": "snax-quiz-questions-items"}).findChildren("li", recursive=False)

    for question in questions_raw:
        q_id = question.div.attrs["data-quizzard-question-id"]
        q_name = question.find(attrs={"class": "snax-quiz-question-title"}).text.strip()
        q_image = ""
        try:
            q_image = question.find(attrs={"class": "snax-quiz-question-media"}).img.attrs["data-src"]
        except:
            pass
        q_options = []
        q_options_raw = question.find(attrs={"class": "snax-quiz-answers-items"}).findChildren("li", recursive=False)
        for q_option_raw in q_options_raw:
            q_option_id = q_option_raw.div.attrs["data-quizzard-answer-id"]
            q_option_text = q_option_raw.find(attrs={"class": "snax-quiz-answer-label-text"}).text.strip()
            q_options.append({"id": q_option_id, "text": q_option_text})
        questions.append({
            "id": q_id,
            "name": q_name,
            "image": q_image,
            "options": q_options
        })
    return questions


def get_test(url):
    r = requests.get(url)
    soap = BeautifulSoup(r.text.replace(u"\ufeff", ""))

    test_id = soap.find(attrs={"class": "snax_quiz"}).attrs["id"].strip().split("-")[1]
    score = soap.find(attrs={"class": "snax-voting-score"}).text.strip()
    name = soap.find(attrs={"class": "entry-title"}).text.strip()
    description = soap.find(attrs={"class": "entry-content"}).p.text.strip()
    category = soap.find(attrs={"class": "entry-category"}).text.strip()
    questions = get_questions(soap)

    test_info = {
        "id": test_id,
        "type": "snax_quiz",
        "url": url,
        "score": score,
        "name": name,
        "description": description,
        "category": category,
        "questions_count": len(questions),
        "questions": questions
    }
    return test_info


def get_raw_result(quiz_id, answers):
    data = {
        "action": "snax_load_quiz_result",
        "quiz_id": quiz_id
    }
    for answer in answers:
        # print(answer)
        data["answers[" + answer['question_id'] + "]"] = answer['answer_id']
    r = requests.post("https://ustaliy.ru/wp-admin/admin-ajax.php", data=data)
    return r.text


def get_parser_result(quiz_id, answers):
    data = get_raw_result(quiz_id, answers)
    data_parsed = json.loads(data)
    soap = BeautifulSoup(data_parsed["args"]["html"].replace(u"\ufeff", ""), "lxml")

    try:
        result1 = soap.find(attrs={"class": "snax-quiz-result-score"}).text.strip()
    except:
        result1 = ""
    try:
        result2 = soap.find(attrs={"class": "snax-quiz-result-title"}).text.strip()
    except:
        result2 = ""
    try:
        image = soap.find(attrs={"class": "snax-quiz-result-media"}).img.attrs["src"].strip()
    except:
        image = ""
    try:
        description = soap.find(attrs={"class": "snax-quiz-result-desc"}).h3.text.strip()
    except:
        description = soap.find(attrs={"class": "snax-quiz-result-desc"}).text.strip()
    if "Рекомендуем лично Вам:" in description:
        description = description.split("Рекомендуем лично Вам:")[0].strip()
    if "Чтобы проверить, как с этим тестом справятся ваши друзья и близкие" in description:
        description = description.split("Чтобы проверить, как с этим тестом справятся ваши друзья и близкие")[0].strip()
    if "Подпишитесь на свежие тесты в VKонтакте," in description:
        description = description.split("Подпишитесь на свежие тесты в VKонтакте,")[0]
    if description == "" and result1 != "" and result2 != "":
        result = result1
        description = result2
    else:
        result = (result1 + "\n\n" + result2).strip()

    description = description.strip()

    return {"result": result, "description": description, "image": image}


def get_test_data(url, channel_id):
    data = {
        'id': None,
        "from-parser": True,
        "results": [],
        "channels": [
            {
                "id": channel_id,
            }
        ],
        "questions": [
        ],
    }

    test = get_test(url)
    name = test['name'].replace('Тест: ', '').upper()

    data['id'] = test['id']
    for q in test["questions"]:
        image = q['image'] if 'image' in q.keys() else None
        data['questions'].append({
            'question': q['name'],
            'id': q['id'],
            'answers': q['options'],
            'image': image,
        })

    return data
