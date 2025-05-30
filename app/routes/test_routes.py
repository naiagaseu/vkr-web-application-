from flask import Blueprint, render_template, redirect, url_for, request, current_app, flash
from app.extensions import db
from datetime import datetime
import json, re
from sqlalchemy import func, or_

from app.models.core_models import Test, Question, Option
from app.models.session_models import Test_session, User_answer, Test_session_skill_result, Test_session_role_result
from app.models.scoring_models import Skill, Role, Option_skill_score, Role_skill_weight



test_bp = Blueprint('test', __name__, url_prefix='/test')



@test_bp.route('/')
def index():
    current_app.logger.debug("Accessing test index page.")
    main_test = Test.query.first()

    if not main_test:
         current_app.logger.error("Test not found in database when accessing test index page.")
         return "Ошибка: Тест не найден в базе данных.", 500

    return render_template('test/index.html', main_test=main_test)


@test_bp.route('/start')
def start_test():
    current_app.logger.debug("Starting new test session.")
    main_test = Test.query.first()
    if not main_test:
         current_app.logger.error("Test not found in database when trying to start new session.")
         return "Ошибка: Тест не найден в базе данных.", 500

    new_session = Test_session(test=main_test, current_question_index=0)
    db.session.add(new_session)
    db.session.commit()

    current_app.logger.info(f"Started new test session with ID: {new_session.id}")

    return redirect(url_for('test.take_session', session_id=new_session.id))


@test_bp.route('/session/<int:session_id>', methods=['GET', 'POST'])
def take_session(session_id):
    current_app.logger.debug(f"Accessing take_session for Session{session_id} with method {request.method}")

    session = Test_session.query.get_or_404(session_id)

    if session.is_completed:
        current_app.logger.warning(f"Attempted to access completed session {session_id}. Redirecting to results.")
        return redirect(url_for('test.show_results', session_id=session.id))

    total_questions_count = Question.query.filter_by(test_id=session.test_id).count()
    current_app.logger.debug(f"Total questions in test {session.test_id}: {total_questions_count}")


    if request.method == 'GET':
        current_app.logger.debug(f"Processing GET request for Session{session_id}. Current index: {session.current_question_index}")

        if session.current_question_index >= total_questions_count and total_questions_count > 0:
            current_app.logger.info(f"GET request for Session{session_id} detected completion state.")
            if not session.is_completed:
                 calculation_successful = calculate_and_save_results(session.id)
                 if not calculation_successful:
                     current_app.logger.error(f"Failed calculation on late GET access for session {session_id}.")
                     return "Произошла ошибка при досчете результатов.", 500

            return redirect(url_for('test.show_results', session_id=session.id))

        if total_questions_count == 0:
             current_app.logger.error(f"Test linked to session {session.id} has no questions.")
             return "Ошибка: В тесте нет вопросов для прохождения.", 500

        if not (0 <= session.current_question_index < total_questions_count):
            current_app.logger.error(f"Session {session.id} has invalid current_question_index {session.current_question_index}. Total questions: {total_questions_count}.")
            return "Ошибка: Некорректный индекс текущего вопроса в сессии.", 500


        question_to_show = Question.query.filter_by(
            test_id=session.test_id,
            order_index=session.current_question_index
        ).first()

        if not question_to_show:
             current_app.logger.error(f"Question with order_index {session.current_question_index} not found for test {session.test_id} in session {session.id}.")
             return "Не удалось загрузить текущий вопрос.", 500

        current_app.logger.debug(f"Rendering question {question_to_show.id} (index {session.current_question_index}) for Session {session.id}")
        return render_template('test/take_session.html',
                               session=session,
                               question=question_to_show,
                               total_questions=total_questions_count
                               )


    elif request.method == 'POST':
        current_app.logger.debug(f"Processing POST request for Session{session_id}. Current index: {session.current_question_index}")
        user_response_data = request.form

        if session.current_question_index >= total_questions_count:
             current_app.logger.warning(f"Received POST for Session{session_id} which is already logically completed (index {session.current_question_index} >= total {total_questions_count}). Redirecting to results.")
             return redirect(url_for('test.show_results', session_id=session.id))

        answered_question_form_key = None
        for key in user_response_data.keys():
            if key.startswith('question_'):
                 try:
                     q_id = int(key.replace('question_', ''))
                     expected_question = Question.query.filter_by(
                         test_id=session.test_id,
                         order_index=session.current_question_index
                     ).first()
                     if expected_question and expected_question.id == q_id:
                          answered_question_form_key = key
                          break
                     current_app.logger.warning(f"POST for Session{session_id} contained unexpected question ID {q_id} at index {session.current_question_index}. Key: {key}")
                 except ValueError:
                     current_app.logger.warning(f"Invalid question ID format in POST form key {key} for Session{session_id}. Skipping.")
                     continue

        if not answered_question_form_key:
            current_app.logger.warning(f"No valid answer data found in POST request for Session{session_id} matching expected question at index {session.current_question_index}. user_response_data: {user_response_data}")
            return redirect(url_for('test.take_session', session_id=session.id))

        try:
            answered_question_id = int(answered_question_form_key.replace('question_', ''))
        except ValueError:
            current_app.logger.error(f"Fatal: Re-parsing question ID from form key failed for Session{session.id}, key {answered_question_form_key}.")
            return "Внутренняя ошибка обработки ответа (парсинг ID).", 500

        answered_question = Question.query.get(answered_question_id)
        if not answered_question:
             current_app.logger.error(f"Fatal: Question ID {answered_question_id} not found on second lookup for Session{session.id}.")
             return "Внутренняя ошибка обработки ответа (вопрос не найден).", 500


        User_answer.query.filter_by(
            test_session_id=session.id,
            question_id=answered_question_id
        ).delete()


        new_user_answer = User_answer(
            test_session=session,
            question=answered_question
        )

        answer_value = user_response_data.get(answered_question_form_key)

        if answered_question.question_type == 'multiple_choice':
            try:
                 chosen_option_id = int(answer_value) if answer_value else None

                 chosen_option = None
                 if chosen_option_id is not None:
                     chosen_option = Option.query.get(chosen_option_id)
                     if not chosen_option or chosen_option.question_id != answered_question.id:
                          current_app.logger.error(f"Invalid option ID {chosen_option_id} submitted for question {answered_question_id} in Session{session.id}. Option not found or mismatch.")
                          db.session.rollback()
                          return redirect(url_for('test.take_session', session_id=session.id))

                 new_user_answer.chosen_option = chosen_option

            except (ValueError, TypeError):
                current_app.logger.error(f"Invalid option ID format received for multiple_choice question {answered_question_id} in Session{session.id}. Value: {answer_value}")
                db.session.rollback()
                return redirect(url_for('test.take_session', session_id=session.id))


        elif answered_question.question_type == 'text_input':
             new_user_answer.text_response = answer_value


        else:
             current_app.logger.warning(f"Unsupported question type {answered_question.question_type} for question {answered_question_id} in Session{session.id}. No answer saved.")
             pass

        db.session.add(new_user_answer)


        session.current_question_index += 1


        try:
            db.session.commit()
            current_app.logger.info(f"Saved answer for Q{answered_question_id} in Session{session_id}. New index: {session.current_question_index}. Total questions: {total_questions_count}")
        except Exception as e:
             db.session.rollback()
             current_app.logger.error(f"Error committing answer and session update for Session{session_id}: {e}", exc_info=True)
             return "Произошла ошибка при сохранении ответа.", 500


        if session.current_question_index >= total_questions_count:
            current_app.logger.info(f"Session {session_id} finished. Starting results calculation.")

            calculation_successful = calculate_and_save_results(session.id)

            if calculation_successful:
                 current_app.logger.info(f"Calculation successful for Session{session_id}. Redirecting to results.")
                 return redirect(url_for('test.show_results', session_id=session.id))
            else:
                 current_app.logger.error(f"Failed to calculate results for session {session_id} after completion.")
                 return "Произошла ошибка при подсчете ваших результатов.", 500


        else:
            current_app.logger.debug(f"Session {session_id} not finished. Redirecting to next question (index {session.current_question_index}).")
            return redirect(url_for('test.take_session', session_id=session.id))



def clean_skill_name(name):
    if not isinstance(name, str):
        return ""
    return re.sub(r'\s*\(.*\)$', '', name)

def clean_interpretation_text(text):
    if not isinstance(text, str):
        return ""
    text = text.replace("По результатам теста ", "")
    text = text.replace("имеет определенную склонность", "Имеется определенная склонность")
    text = text.replace("демонстрирует выраженную склонность", "Имеется выраженная склонность")
    text = text.replace("требует развития", "Требуется развитие")
    return text

@test_bp.route('/session/<int:session_id>/results')
def show_results(session_id):
    current_app.logger.info(f"Accessing results page for session {session_id}.")
    session = Test_session.query.get_or_404(session_id)

    if not session.is_completed:
        current_app.logger.warning(f"Attempted to access results for incomplete session {session_id}. Trying to recalculate.")
        calculation_successful = calculate_and_save_results(session.id)
        if not calculation_successful:
            current_app.logger.error(f"Recalculation failed for session {session.id} on results page access.")
            return "Произошла ошибка при загрузке результатов (пересчет не удался).", 500


    skill_results_db = db.session.query(Test_session_skill_result).options(
        db.joinedload(Test_session_skill_result.skill)
    ).filter_by(test_session_id=session.id).all()
    skill_results_db = sorted(skill_results_db, key=lambda res: res.skill.name if res.skill else '')


    try:
        role_results_db = db.session.query(Test_session_role_result).options(
            db.joinedload(Test_session_role_result.role).joinedload(Role.role_skill_weights).joinedload(Role_skill_weight.skill)
        ).filter_by(test_session_id=session.id).all()
        role_results_db = sorted(role_results_db, key=lambda res: res.role.name if res.role else '')
    except Exception as e:
        current_app.logger.error(f"Error loading role results with eager loading for session {session.id}: {e}", exc_info=True)
        return "Ошибка загрузки данных результатов по ролям.", 500


    role_results_for_template = []

    for res in role_results_db:
         if res.role:
             key_competencies_names = []
             if res.role.role_skill_weights:
                  key_competencies_names = [
                     clean_skill_name(weight.skill.name) for weight in res.role.role_skill_weights

                     if weight.skill and weight.skill.type == 'Hard'
                  ]
             key_competencies_names = sorted(key_competencies_names)

             role_results_for_template.append({
                 'role_name': res.role.name,
                 'integral_score': res.integral_score,
                 'key_competencies': key_competencies_names
             })
         else:
              current_app.logger.warning(f"Role result {res.id} for session {session.id} is linked to a non-existent role during template data prep.")
              pass

    role_results_for_template = sorted(role_results_for_template, key=lambda item: item['role_name'])


    soft_skill_results_with_interpretation = []
    hard_skill_results_for_template = []

    LOW_LEVEL_THRESHOLD = 20.0
    MEDIUM_LEVEL_THRESHOLD = 55.0
    def interpret_soft_skill_score(score):
         if score < LOW_LEVEL_THRESHOLD: return "По результатам теста требует развития"
         elif score <= MEDIUM_LEVEL_THRESHOLD: return "По результатам теста имеет определенную склонность"
         else: return "По результатам теста демонстрирует выраженную склонность"

    for res in skill_results_db:
         if res.skill:
             if res.skill.type == 'Soft':
                 soft_skill_results_with_interpretation.append({
                     'skill_name': res.skill.name,

                     'interpretation': clean_interpretation_text(interpret_soft_skill_score(res.normalized_score))
                 })
             elif res.skill.type == 'Hard':
                 hard_skill_results_for_template.append({
                     'skill_name': res.skill.name,
                     'normalized_score': res.normalized_score,
                     'obtained_primary_score': res.obtained_primary_score,
                     'max_possible_primary_score': res.max_possible_primary_score
                 })
         pass


    hard_skill_results_for_template = sorted(hard_skill_results_for_template, key=lambda x: x.get('skill_name', ''))
    soft_skill_results_with_interpretation = sorted(soft_skill_results_with_interpretation, key=lambda x: x.get('skill_name', ''))


    chart_labels = [res['skill_name'] for res in hard_skill_results_for_template]
    chart_data = [res['normalized_score'] for res in hard_skill_results_for_template]

    if hard_skill_results_for_template:
        chart_data_full = {
            'labels': chart_labels,
            'datasets': [{
                'label': 'Ваш профиль Hard Skills',
                'data': chart_data,
                'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                'borderColor': 'rgb(54, 162, 235)',
                'pointBackgroundColor': 'rgb(54, 162, 235)',
                'pointBorderColor': '#fff',
                'pointHoverBackgroundColor': '#fff',
                'pointHoverBorderColor': 'rgb(54, 162, 235)',
                'borderWidth': 2
            }]
        }
    else:
        current_app.logger.warning(f"No Hard Skill results found for session {session.id}. Cannot render radar chart.")
        chart_data_full = {'labels': [], 'datasets': []}


    current_app.logger.debug(f"Rendering results page for session {session.id}. Role results count: {len(role_results_for_template)}. Hard Skill results count: {len(hard_skill_results_for_template)}. Soft Skill results count: {len(soft_skill_results_with_interpretation)}")

    return render_template('test/results.html',
                           session=session,
                           role_results=role_results_for_template,
                           hard_skill_results=hard_skill_results_for_template,
                           soft_skill_results_with_interpretation=soft_skill_results_with_interpretation,
                           chart_data_full=chart_data_full
                           )


def calculate_and_save_results(session_id):
    current_app.logger.info(f"Starting results calculation for session {session_id}")

    session = Test_session.query.get(session_id)

    if not session:
        current_app.logger.error(f"Session with ID {session_id} not found for results calculation.")
        return False


    try:
        Test_session_skill_result.query.filter_by(test_session_id=session.id).delete()
        Test_session_role_result.query.filter_by(test_session_id=session.id).delete()


        obtained_scores_query = db.session.query(
            Option_skill_score.skill_id,
            func.sum(Option_skill_score.score).label('sum_score')
        ).join(Option).join(User_answer).filter(
            User_answer.test_session_id == session.id,
            User_answer.chosen_option_id.isnot(None)
        ).group_by(Option_skill_score.skill_id).all()

        obtained_primary_scores = {item.skill_id: item.sum_score for item in obtained_scores_query}
        current_app.logger.debug(f"Session {session.id} - Obtained primary scores per skill (query): {obtained_primary_scores}")


        current_test = session.test
        if not current_test:
             current_app.logger.error(f"Test object not found for session {session.id} during results calculation.")
             return False

        all_questions_options_scores = db.session.query(
             Question, Option, Option_skill_score
        ).select_from(Question).join(Option).join(Option_skill_score).filter(
             Question.test_id == current_test.id
        ).all()

        max_skill_score_per_question = {}
        for question, option, score_entry in all_questions_options_scores:
             q_id = question.id
             s_id = score_entry.skill_id
             score = score_entry.score

             if q_id not in max_skill_score_per_question:
                 max_skill_score_per_question[q_id] = {}

             if s_id not in max_skill_score_per_question[q_id] or score > max_skill_score_per_question[q_id][s_id]:
                  max_skill_score_per_question[q_id][s_id] = score

        max_possible_primary_scores = {}
        for q_id, skill_scores in max_skill_score_per_question.items():
             for s_id, max_score in skill_scores.items():
                 max_possible_primary_scores[s_id] = max_possible_primary_scores.get(s_id, 0.0) + max_score


        current_app.logger.debug(f"Session {session.id} - Max possible primary scores per skill in test: {max_possible_primary_scores}")


        all_skills = Skill.query.all()
        all_skills_map = {skill.id: skill for skill in all_skills}

        normalized_skill_scores = {}

        for skill in all_skills:
             skill_id = skill.id
             skill_name = skill.name

             obtained_score = obtained_primary_scores.get(skill_id, 0.0)
             max_score = max_possible_primary_scores.get(skill_id, 0.0)

             normalized_score = 0.0
             if max_score > 0:
                 normalized_score = (obtained_score / max_score) * 100.0
                 normalized_score = round(min(normalized_score, 100.0), 2)

             normalized_skill_scores[skill_id] = normalized_score

             skill_result = Test_session_skill_result(
                 test_session=session,
                 skill=skill,
                 obtained_primary_score=obtained_score,
                 max_possible_primary_score=max_score,
                 normalized_score=normalized_score
             )
             db.session.add(skill_result)


        all_roles_list = Role.query.all()

        for role in all_roles_list:
             integral_score = 0.0
             total_weight = 0.0

             for role_skill_weight in role.role_skill_weights:
                 skill = role_skill_weight.skill
                 weight = role_skill_weight.weight

                 if skill and skill.type == 'Hard':
                     skill_normalized_score = normalized_skill_scores.get(skill.id, 0.0)
                     integral_score += (skill_normalized_score * weight)
                     total_weight += weight

             role_result = Test_session_role_result(
                 test_session=session,
                 role=role,
                 integral_score=round(integral_score, 2)
             )
             db.session.add(role_result)
             current_app.logger.debug(f" Session {session.id} - Role '{role.name}': Integral Score = {integral_score:.2f} (Sum of weights for contributing Hard Skills: {total_weight:.2f})")


        session.is_completed = True
        session.end_time = datetime.utcnow()


        db.session.commit()


        current_app.logger.info(f"Results successfully calculated and saved for session {session_id}. Session marked as completed.")
        return True


    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Critical error during results calculation for Session{session_id}: {e}", exc_info=True)
        return False
