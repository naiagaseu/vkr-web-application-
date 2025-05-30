# MYPROJECT/load_initial_data.py

import json
import os
from flask import Flask # Для создания контекста приложения
from app import create_app # Для получения экземпляра приложения через фабрику
from app.extensions import db # Импортируем объект db напрямую

# Импортируем ВСЕ классы моделей из конкретных модулей в app.models
# Flask-SQLAlchemy и Flask-Migrate должны "увидеть" все определения моделей
# для правильной работы (связи, создание таблиц и т.д.), даже если в этом скрипте
# мы напрямую работаем только с частью из них (статическими данными).
from app.models.core_models import Test, Question, Option
from app.models.scoring_models import Skill, Role, Option_skill_score, Role_skill_weight
from app.models.session_models import Test_session, User_answer, Test_session_skill_result, Test_session_role_result
# Если у тебя все еще есть модель User и она определена в app/models/users.py, импортируй ее тоже
# from app.models.users import User


# Укажи путь к папке с твоими JSON файлами. Предполагается, что она называется 'data'
# и находится в корневой директории твоего проекта (рядом со скриптом load_initial_data.py).
JSON_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')

def load_json_file(filename):
    """Вспомогательная функция для загрузки данных из JSON файла."""
    filepath = os.path.join(JSON_DATA_PATH, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            print(f"  Loading file: {filepath}")
            return json.load(f)
    except FileNotFoundError:
        print(f"  Error: File not found at {filepath}. Skipping.")
        return None
    except json.JSONDecodeError:
        print(f"  Error: Could not decode JSON from {filepath}. Check file format. Skipping.")
        return None
    except Exception as e:
        print(f"  An unexpected error occurred while loading {filepath}: {e}. Skipping.")
        return None


def load_initial_data():
    """Основная функция для загрузки всех статических данных в БД."""

    app = create_app() # Использование application factory create_app из app/__init__.py

    try: # <-- Начало большого try блока для всего процесса загрузки
        with app.app_context():
            print("Starting database static data loading...")

            # --- ОЧЕНЬ ВАЖНОЕ ПРИМЕЧАНИЕ ДЛЯ РАЗРАБОТКИ ---
            # В следующем блоке кода (закомментированном) есть возможность очистить
            # СУЩЕСТВУЮЩИЕ СТАТИЧЕСКИЕ ДАННЫЕ перед загрузкой.
            # Раскомментируй и используй его ТОЛЬКО если ты намеренно хочешь
            # начать заполнение этих таблиц с нуля КАЖДЫЙ РАЗ при запуске скрипта.
            # Это полезно в процессе активной разработки теста/методики.
            # ВНИМАНИЕ! ЭТО БУДЕТ БЕЗВОЗВРАТНО УДАЛЕНО ВСЁ ИЗ ЭТИХ ТАБЛИЦ!
            # Убедись, что приложение в режиме разработки, используя app.config.get('ENV').
            # Если ты не устанавливаешь ENV, можно убрать проверку if...
            # -----------------------------------------------------------
            
            #if app.config.get('ENV') == 'development' or True: # <-- Отступ X
             #   print("\n[DEVELOPMENT MODE] Deleting existing static data for clean load...") # <-- Отступ X
              #  try: # <-- Отступ X (Блок try для удаления)
                    # Порядок удаления важен!
                    # Удаляем Option_skill_score -> Option -> Question для данного теста
                    # (Не трогаем статику для Test, Role, Skill, Role_skill_weight и динамические таблицы результатов!)

               #     db.session.execute(Option_skill_score.__table__.delete()) # <-- Отступ X+4 пробела
              #      db.session.execute(Option.__table__.delete())           # <-- Отступ X+4 пробела
              #      db.session.execute(Question.__table__.delete())         # <-- Отступ X+4 пробела

                    # Если ты хочешь удалить также Role_skill_weight:
                    # db.session.execute(Role_skill_weight.__table__.delete()) # <-- Отступ X+4 пробела

                    # Не удаляем Test, Role, Skill если они уже загружены и не надо их менять!

              #      db.session.commit() # <-- Отступ X+4 пробела. Коммитит удаление!
               #     print("  Selected static data deleted successfully.") # <-- Отступ X+4 пробела

              #  except Exception as e: # <-- Отступ X. Except для try УДАЛЕНИЯ.
              #      db.session.rollback() # <-- Отступ X+4 пробела. Код внутри except.
              #      print(f"  Error deleting selected static data: {e}") # <-- Отступ X+4 пробела
              #      traceback.print_exc() # <-- Отступ X+4 пробела
              #      print("-" * 30) # <-- Отступ X+4 пробела
            # -----------------------------------------------------------


            # Используем словари для хранения объектов после их создания/нахождения,
            # чтобы быстро находить связанные объекты по имени при загрузке других данных.
            skills_map = {}
            roles_map = {}
            tests_map = {}


            # 1. Загрузка Skills (Навыки/Компетенции)
            print("Loading Skills...")
            skills_data = load_json_file('skills.json') # Убедись, что файл называется именно так и лежит в папке 'data'
            if skills_data is not None:
                try:
                    for item in skills_data:
                        # Проверка базовой структуры элемента JSON
                        if not isinstance(item, dict) or 'name' not in item or 'type' not in item:
                             print(f"  Skipping invalid item format: {item}")
                             continue

                        # Ищем навык по имени. Если его нет - создаем.
                        skill = Skill.query.filter_by(name=item['name']).first()
                        if skill is None:
                             skill = Skill(name=item['name'], type=item['type'])
                             db.session.add(skill)
                             db.session.flush() # Нужен flush, чтобы объект получил ID перед добавлением в словарь
                             print(f"  Added skill: {skill.name} ({skill.type})")
                        else:
                            print(f"  Skill already exists: {skill.name}")

                        skills_map[skill.name] = skill # Сохраняем в словарь по имени для быстрого доступа
                    db.session.commit()
                    print("Skills loading finished.")
                except Exception as e:
                     db.session.rollback() # Откатываем изменения при ошибке
                     print(f"  Error loading skills: {e}")
            else:
                 print("Skipped loading skills due to file error.")


            # 2. Загрузка Roles (Роли) И Role_skill_weight (Веса навыков по ролям)
            print("\nLoading Roles and Role Skill Weights...")
            roles_weights_data = load_json_file('roles_weights.json') # Убедись, что файл называется именно так и лежит в папке 'data'
            if roles_weights_data is not None:
                try:
                     # Проходимся по ролям в JSON файле (ключи верхнего уровня являются именами ролей)
                    if not isinstance(roles_weights_data, dict):
                         print(f"  Skipping loading roles and weights: expected a dictionary at top level, but got {type(roles_weights_data)}")
                    else:
                        for role_name, skill_weights in roles_weights_data.items():
                            # Ищем роль по имени. Если нет - создаем.
                            role = Role.query.filter_by(name=role_name).first()
                            if role is None:
                                role = Role(name=role_name) # Модель Role имеет только поле 'name', согласно твоему ERD. Можешь добавить 'description'.
                                db.session.add(role)
                                db.session.flush()
                                print(f"  Added role: {role.name}")
                            else:
                                print(f"  Role already exists: {role.name}")

                            roles_map[role.name] = role # Сохраняем в словарь по имени

                            # Если успешно обработали роль, проходимся по навыкам и их весам для этой роли
                            if isinstance(skill_weights, dict): # Убедимся, что значение под именем роли - это словарь весов
                                 for skill_name, weight in skill_weights.items():
                                    # Проверка значения веса
                                    if not (isinstance(weight, (int, float)) and 0 <= weight <= 1): # Вес должен быть числом от 0 до 1
                                         print(f"    Skipping invalid weight value {weight} for Skill '{skill_name}' in Role '{role_name}'.")
                                         continue

                                    # Ищем объект Skill из загруженных ранее, используя skills_map
                                    skill = skills_map.get(skill_name)

                                    if skill:
                                        # Проверяем, есть ли уже такой вес для этой роли и навыка
                                        existing_weight = Role_skill_weight.query.filter_by(
                                            role=role,
                                            skill=skill
                                        ).first()
                                        if existing_weight is None:
                                            # Создаем новую запись Role_skill_weight
                                            role_skill_weight = Role_skill_weight(
                                                role=role,
                                                skill=skill,
                                                weight=float(weight) # Приводим вес к типу float на всякий случай
                                            )
                                            db.session.add(role_skill_weight)
                                            #print(f"    Added weight: Role '{role.name}' -> Skill '{skill.name}' = {weight}") # Можно включить для детального лога
                                        # else: # Опционально: вывести сообщение, если вес уже есть
                                             # print(f"    Weight already exists for Role '{role.name}' -> Skill '{skill.name}'")
                                    else:
                                         print(f"    WARNING: Skill '{skill_name}' not found for Role '{role_name}'. Check skills.json and role_weights.json for consistency. Skipping weight.")

                            else:
                                print(f"  WARNING: Skill weights data for role '{role_name}' is not a dictionary: {skill_weights}. Skipping weights for this role.")

                    db.session.commit() # Коммитим роли и веса навыков
                    print("Roles and Role Skill Weights loading finished.")
                except Exception as e:
                     db.session.rollback() # Откатываем изменения при ошибке
                     print(f"  Error loading roles or weights: {e}")
            else:
                 print("Skipped loading roles and weights due to file error.")


            # 3. Загрузка Tests (Тест) - т.к. тест один
            print("\nLoading Test...")
            tests_data = load_json_file('tests.json') # Убедись, что файл называется именно так и лежит в папке 'data'
            if tests_data and isinstance(tests_data, list) and len(tests_data) > 0:
                 test_info = tests_data[0] # Берем первый элемент из списка, предполагая один тест
                 test = None
                 try:
                     test = Test.query.filter_by(name=test_info.get('name')).first()
                     if test is None and test_info.get('name'):
                         test = Test(name=test_info['name'], description=test_info.get('description', '')) # Загружаем описание, если есть
                         db.session.add(test)
                         db.session.flush() # Нужен flush, чтобы получить ID теста
                         print(f"  Added test: {test.name}")
                     elif test:
                         print(f"  Test already exists: {test.name}")
                     else:
                         print("  Skipped adding test: Invalid data in tests.json")

                     if test:
                         tests_map[test.name] = test # Сохраняем объект теста в словарь для использования дальше
                         # Опционально можно сохранить тест в переменную с более понятным именем, если он один
                         # Например: main_test = test
                         db.session.commit() # Коммитим тест

                         print("Test loading finished.")
                     else:
                          print("Skipped Test loading due to data error in tests.json.") # Тест не удалось загрузить из JSON

                 except Exception as e:
                      db.session.rollback()
                      print(f"  Error loading test: {e}")

            else:
                 print("Skipped loading test due to file error or empty/invalid file.")
                 # Если тест не загрузился, мы не сможем загрузить вопросы, связанные с ним.


            # 4. Загрузка Questions, Options, and Option_skill_score
            # Этот раздел выполняется ТОЛЬКО если тест был успешно загружен
            print("\nLoading Questions, Options, and Option Skill Scores...")
            questions_data = load_json_file('questions.json') # Убедись, что файл называется именно так и лежит в папке 'data'

            # Ищем объект теста, к которому привязывать вопросы. Т.к. у нас один тест,
            # пробуем получить его из tests_map или ищем в БД по имени.
            main_test = next(iter(tests_map.values()), None) # Получить первый (и единственный) объект теста из словаря
            if not main_test and questions_data is not None: # Если теста нет, но файл вопросов есть, пробуем найти тест по имени
                 # Если по какой-то причине теста нет в словаре tests_map,
                 # но tests.json был считан, попробуем найти тест по его имени из JSON, если оно есть
                 test_name_from_json = tests_data[0].get('name') if tests_data and isinstance(tests_data, list) and len(tests_data) > 0 else None
                 if test_name_from_json:
                     main_test = Test.query.filter_by(name=test_name_from_json).first()
                     if main_test:
                          print(f"  Found existing test '{test_name_from_json}' in DB to link questions.")
                     else:
                          # ВНИМАНИЕ: Если дошли сюда, значит тест по имени из tests.json
                         # не удалось загрузить или найти. Не сможем связать вопросы.
                         print(f"  ERROR: Test with name '{test_name_from_json}' not found in DB to link questions! Skipping questions loading.")


            # Продолжаем загрузку вопросов только если questions_data не пустой и main_test объект доступен
            if questions_data is not None and main_test:
                 try:
                     if not isinstance(questions_data, list):
                          print(f"  Skipping loading questions: expected a list at top level, but got {type(questions_data)}")
                     else:
                        # Используем enumerate, чтобы получить индекс (order_index) каждого вопроса
                        for index, q_data in enumerate(questions_data): # <--- ВОТ ЭТО ИЗМЕНЕНИЕ! Используем enumerate
                            q_text = q_data.get('text')

                            # Проверка базовой структуры вопроса
                            if not isinstance(q_data, dict) or not q_text or 'options' not in q_data:
                                print(f"  Skipping invalid question format (missing text or options): {q_data}")
                                continue

                            # QUESTION_TYPE будет браться либо из JSON ('question_type' или 'type'),
                            # либо дефолтный 'multiple_choice'. Этот код остался из прошлой версии.
                            question_type_from_json = q_data.get('question_type')
                            if question_type_from_json is None:
                                 question_type_from_json = q_data.get('type') # Попробуем старый ключ 'type'

                            # Ищем вопрос по test, text И order_index, или просто по test и text
                            # Т.к. order_index новое поле и может быть еще 0 для всех старых вопросов,
                            # безопаснее искать только по test и text для нахождения СУЩЕСТВУЮЩИХ вопросов.
                            # НОВЫМ ВОПРОСАМ мы явно присвоим порядок.
                            question = Question.query.filter_by(
                                test=main_test, # Привязываем к главному тесту
                                text=q_text
                            ).first()

                            if question is None:
                                # Создаем НОВЫЙ вопрос
                                question = Question(
                                    test=main_test,
                                    text=q_text,
                                    question_type=question_type_from_json if question_type_from_json is not None else 'multiple_choice',
                                    order_index=index # <--- ПРИСВАИВАЕМ order_index НА ОСНОВЕ ПОРЯДКА В JSON!
                                )
                                db.session.add(question)
                                db.session.flush() # Нужен flush, чтобы получить ID вопроса для вариантов
                                #print(f"  Added question (index {index}): {question.text[:80]}...") # Детальный лог
                            else:
                                # Вопрос уже существует. ОБНОВЛЯЕМ order_index для него.
                                # (Это нужно, если ты перезапускаешь скрипт после миграции, и вопросы уже есть,
                                # но им нужно назначить порядок)
                                question.order_index = index # <--- ОБНОВЛЯЕМ order_index ДЛЯ СУЩЕСТВУЮЩЕГО ВОПРОСА
                                db.session.add(question) # Добавляем для сохранения изменений
                                #print(f"  Question already exists (index {index}), updating order: {question.text[:80]}...") # Детальный лог


                            # Загрузка вариантов ответов (Options)
                            # Этот подблок остается почти без изменений, он привязывается к текущему 'question'
                            options_data = q_data.get('options')
                            if options_data and isinstance(options_data, list):
                                for opt_data in options_data:
                                    # Проверка базовой структуры варианта ответа
                                    if not isinstance(opt_data, dict) or 'text' not in opt_data or 'skill_scores' not in opt_data: # skill_scores ожидается
                                         print(f"    Skipping invalid option format for question '{q_text[:50]}...': {opt_data}")
                                         continue

                                    opt_text = opt_data['text']
                                    if not opt_text: # Проверка наличия текста варианта
                                         print(f"    Skipping empty option text for question '{q_text[:50]}...': {opt_data}")
                                         continue

                                    # Ищем вариант ответа, связанный с этим вопросом, по тексту. Если нет - создаем.
                                    option = Option.query.filter_by(
                                        question=question, # Привязываем к текущему вопросу
                                        text=opt_text
                                    ).first()
                                    if option is None:
                                        option = Option(
                                            question=question, # Привязываем к текущему вопросу
                                            text=opt_text
                                        )
                                        db.session.add(option)
                                        db.session.flush() # Нужен flush, чтобы получить ID варианта для Option_skill_score
                                        #print(f"      Added option: {option.text[:80]}...") # Детальный лог
                                    # else:
                                        # pass # print(f"      Option already exists: {option.text[:80]}...") # Детальный лог


                                    # Загрузка баллов Option_skill_score для этого варианта
                                    scores_data = opt_data.get('skill_scores') # ИСПОЛЬЗУЕМ ИМЕННО 'skill_scores'
                                    if scores_data is not None and type(scores_data) is list:
                                        # Для избежания дубликатов Option_skill_score при повторном запуске
                                        # и при необходимости обновить баллы из JSON
                                        existing_oss_map = { (oss.option_id, oss.skill_id): oss for oss in option.option_skill_scores } # Маппинг по парам ID для поиска

                                        for score_item in scores_data:
                                            # Проверка структуры объекта балла
                                            if not isinstance(score_item, dict) or 'skill_name' not in score_item or 'score' not in score_item:
                                                print(f"        Skipping invalid score item format for option '{opt_text[:50]}...': {score_item}")
                                                continue

                                            skill_name = score_item['skill_name']
                                            score_value = score_item['score']

                                            # Проверка значения балла
                                            if not (isinstance(score_value, (int, float)) and score_value in [0.0, 0.5, 1.0, 0, 0.5, 1]):
                                                 print(f"        Skipping invalid score value {score_value} for Skill '{skill_name}' in Option '{opt_text[:50]}...'. Must be 0, 0.5 or 1.")
                                                 continue

                                            # Ищем объект Skill по имени
                                            skill = skills_map.get(skill_name)

                                            if skill:
                                                # Проверяем, есть ли уже такая запись Option_skill_score
                                                oss_key = (option.id, skill.id)
                                                existing_oss = existing_oss_map.get(oss_key) # Ищем по маппингу

                                                if existing_oss is None:
                                                    # Создаем новую запись Option_skill_score
                                                    oss = Option_skill_score(
                                                        option=option,
                                                        skill=skill,
                                                        score=float(score_value) # Убедимся, что сохраняется как float
                                                    )
                                                    db.session.add(oss)
                                                    #print(f"          Added score: Option '{option.text[:30]}...' -> Skill '{skill.name[:30]}...' = {score_value}") # Детальный лог
                                                elif existing_oss.score != float(score_value):
                                                    # Обновляем балл, если он изменился в JSON
                                                     existing_oss.score = float(score_value)
                                                     db.session.add(existing_oss) # Отмечаем для сохранения
                                                     print(f"          Updated score: Option '{option.text[:30]}...' -> Skill '{skill.name[:30]}...' = {score_value}")
                                                # else:
                                                     # print(f"          Score already exists and is the same: Option '{option.text[:30]}...' -> Skill '{skill.name[:30]}...'")
                                            else:
                                                print(f"        WARNING: Skill '{skill_name}' not found for Option '{opt_text[:50]}...'. Check skills.json and questions.json for consistency. Skipping score.")

                            else:
                                    if 'skill_scores' not in opt_data:
                                         print(f"      WARNING: Option '{opt_text[:50]}...' is missing 'skill_scores' key. Full option data: {opt_data}. Skipping scores loading.")
                                    elif scores_data is None: # Отдельная проверка на None
                                         print(f"      WARNING: 'skill_scores' for option '{opt_text[:50]}...' is None. Full option data: {opt_data}. Skipping scores loading.")
                                    else: # Ловим случаи, когда значение есть, но не является списком и не None
                                         print(f"      WARNING: 'skill_scores' for option '{opt_text[:50]}...' exists but is not a list or is None. Value: {scores_data}. Type: {type(scores_data)}. Skipping scores loading.")
                                         # print(f"      Full option data for inspection: {opt_data}") # Опционально

                                    pass

                        else: # Если у вопроса нет списка 'options' или он пустой/некорректный
                             # print(f"    Skipped loading options for question '{q_text[:50]}...': 'options' not a list or empty or invalid. Assuming it's a text input question?")
                             pass

                    # Коммит всех изменений, добавленных в этом блоке (для вопросов, вариантов, разбалловки)
                        db.session.commit() # Делаем commit после цикла по всем вопросам
                        print("Questions, Options, and Option Skill Scores loading finished.")

                 except Exception as e:
                      db.session.rollback() # Откатываем изменения при ошибке
                      print(f"  Error loading questions, options, or scores: {e}")
                      print("  Rolled back session due to error.")

            else: # Этот блок else обрабатывает случай, когда questions_data равен None или main_test равен None
                 if questions_data is None:
                      print("Skipped loading questions due to file error or empty file.")
                 elif main_test is None:
                      print("Skipped loading questions: Test object not loaded from tests.json or not found in DB.")


            print("\n--- Initial database static data loading completed! ---") # Финальное сообщение скрипта
            print(f"Check your database to confirm data was loaded into tables: {', '.join([m.__tablename__ for m in [Skill, Role, Test, Question, Option, Option_skill_score, Role_skill_weight]])}")

    except Exception as e: # <-- Конец большого try блока, начало except для всего процесса загрузки
            print("\n--- ERROR: An unexpected error occurred during data loading ---")
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {e}")
            import traceback # Импортируем traceback для полного вывода
            traceback.print_exc() # Печатаем полный traceback
            # Возможно, db.session активна и требует отката
            try:
                if db.session.dirty or db.session.new or db.session.deleted:
                     print("Attempting to rollback database session...")
                     db.session.rollback() # Попробуем откатить сессию при ошибке
                     print("Session rolled back.")
            except Exception as rollback_e:
                 print(f"Error during session rollback: {rollback_e}")

    print("\n--- load_initial_data function finished ---") # <-- Принт в конце функции load_initial_data

# --- ВОТ ЭТОТ БЛОК if __name__ == '__main__': НУЖНО ДОБАВИТЬ В САМЫЙ КОНЕЦ ФАЙЛА ---
# Этот блок позволяет запустить функцию load_initial_data, когда вы выполняете
# скрипт напрямую из командной строки: python load_initial_data.py
#
# Перед запуском необходимо убедиться, что Flask приложение доступно.
# Это обычно делается установкой переменной окружения FLASK_APP.
# Например, в терминале:
# export FLASK_APP=app  (для Linux/macOS)
# set FLASK_APP=app     (для Windows cmd)
# $env:FLASK_APP="app"  (для Windows PowerShell)
#
# Либо добавьте FLASK_APP=app в файл .flaskenv в корне проекта,
# и Flask CLI подхватит ее автоматически.

if __name__ == '__main__':
    print("Attempting to run initial data loading script from __main__ block.")
    # Проверка переменной FLASK_APP для помощи пользователю (опционально, но полезно)
    import os # Импорт os нужен для os.environ.get()
    if os.environ.get('FLASK_APP') != 'app':
        print("\n--- WARNING: FLASK_APP environment variable not set or incorrect. ---")
        print("Please set FLASK_APP=app in your terminal or .flaskenv file.")
        print("Example: export FLASK_APP=app  (on Linux/macOS)")
        print("Loading might fail or connect to wrong DB without it.")
        print("-" * 40, "\n")

    load_initial_data() # <-- ВОТ ЭТОТ ВЫЗОВ ЗАПУСКАЕТ ВСЮ РАБОТУ!

    print("\n__main__ block finished.")