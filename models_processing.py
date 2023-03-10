import os
import dill
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from tqdm import tqdm

import text_processing
import common_vars

# Удобнее загрузить таблицу в самом начале и потом обращаться к этой переменной
df_q = pd.read_excel("questions.xlsx", index_col=None, engine='openpyxl')
full_df = pd.read_excel("train_data.xlsx", index_col=None, engine='openpyxl')
full_df = full_df[~full_df["answer"].isna()]
common_vars.TEST_QUESTIONS = list(full_df["question"].unique())

models_quantity = 4
forcibly_rebuild_models = False

for model_num in range(1, models_quantity + 1):
    if not os.path.isfile(f"model{model_num}.mdl") or forcibly_rebuild_models:
        # Если не обнаружили файл хотя бы одной модели,
        # то это значит, что нужно обработать данные:
        full_df = full_df.rename(columns={"answer": "X"})
        full_df["X"] = full_df.X.str.lower().replace("\n", "").replace("  ", " ").replace(r"[^\w\s]", "", regex=True)

        print("Производится предобработка текстов для обучения модели:")
        for idx in tqdm(full_df.index):
            processed_text = full_df[full_df.index == idx]["X"].values[0]
            processed_text = text_processing.preprocess_text(processed_text)
            if not processed_text.replace(" ", ""):
                # Случай, когда все слова из ответа были исключены.
                # Нно так нельзя, поэтому добавим слово
                processed_text = "слово"

            full_df.loc[(full_df.index == idx), "X"] = processed_text
        print("Предобработка завершена")

        # Прерываем цикл, так как данные уже загрузили.
        break


def get_data(num):
    # Для каждой модели используется свой столбец.
    # Выбираем его и возвращаем таблицу из двух столбцов: X и y.
    mark_column_name = f"grade{num}"
    data = full_df[["question", "X", mark_column_name]]
    data = data.rename(columns={mark_column_name: "y"})
    data.fillna(0, inplace=True)
    return data


def get_model(num):
    model_file_name = f"model{num}.mdl"
    if os.path.isfile(model_file_name) and not forcibly_rebuild_models:
        # Если файл этой модели есть, то используем его:
        with open(model_file_name, 'rb') as hfile:
            model_branch = dill.load(hfile)
    else:
        # Если файла этой модели нет, то создаём модель.
        # Одна модель - это набор моделей отдельно обученных для каждого (!) вопроса.
        # Сохраняем это всё в словаре, где ключ - это вопрос.
        print("Отсутствует одна из моделей.")
        print("Обучим и подготовим для использования:")
        local_full_data = get_data(num)
        model_branch = dict()
        for one_question in df_q.values:
            one_question = one_question[0]
            text_clf = Pipeline([('tfidf', TfidfVectorizer()), ('clf', SGDClassifier(loss='hinge')), ])
            # Отфильтруем из общих данных только данные для этого вопроса:
            data = local_full_data[(local_full_data["question"] == one_question) & (local_full_data["y"] >= -1) & (local_full_data["y"] <= 1)]

            # ...и учим уже на этих данных, но только если есть строки:
            if data.shape[0] != 0:
                text_clf.fit(data.X, data.y)
                # и сохраняем эту подмодель со ссылкой на вопрос:
                model_branch[one_question] = text_clf

        # ... и сохраняем в файл для повторного использования в следующий раз:
        with open(model_file_name, 'wb') as file:
            dill.dump(model_branch, file)

    return model_branch


def prepare_models(quantity=models_quantity):
    models_group = []
    for num in range(1, quantity + 1):
        models_group = models_group + [get_model(num)]

    common_vars.PREPARED_MODELS = models_group

    print("Модели загружены.")


def get_models_predictions(question_text=None, answer=None):
    # На оценку влияет "знак", его нужно получить и нужно учитывать:
    sign = df_q[df_q["question"] == question_text]["sign"].values[0]
    rating = 0
    ratings = []
    answer = text_processing.preprocess_text(answer)

    for one_model in common_vars.PREPARED_MODELS:
        one_rating = one_model[question_text].predict([answer])[0] * sign
        ratings = ratings + [one_rating]
        rating += one_rating

    return ratings


def get_models_predictions_and_print(question_text, answer):
    rating = get_models_predictions(question_text=question_text, answer=answer)
    print("------------------------------")
    print(question_text, answer)
    print("All ratings:", rating)


if __name__ == '__main__':
    prepare_models()
    q = "03. Больше всего я люблю, когда учитель..."
    get_models_predictions_and_print(q, "кричать")
    get_models_predictions_and_print(q, "мычать")
    get_models_predictions_and_print(q, "выть")
    get_models_predictions_and_print(q, "библиотекарь")

    get_models_predictions_and_print(q, "здесь интересно учиться")
