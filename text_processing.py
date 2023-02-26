# Необходимо один раз загрузить корпус "стоп слов".
# import nltk
# nltk.download("stopwords")

from nltk.corpus import stopwords
from pymystem3 import Mystem
from string import punctuation

mystem = Mystem()
try:
    print("Подготавливаем стоп-слова.")
    russian_stopwords = set(stopwords.words("russian")) ^ {"не", "нет", "хорошо"}
except:
    print("Загружаем стоп-слова...")
    import nltk
    nltk.download("stopwords")
    russian_stopwords = set(stopwords.words("russian")) ^ {"не", "нет", "хорошо"}


def preprocess_text(text):
    tokens = mystem.lemmatize(text.lower())
    tokens = [token for token in tokens if token not in russian_stopwords and token != " " and token.strip() not in punctuation]

    if ("не" in tokens) or ("нет" in tokens):
        tokens = tokens + ["negative"]
    else:
        tokens = tokens + ["positive"]

    text = " ".join(tokens)

    return text


if __name__ == '__main__':
    print(preprocess_text("Сегодня я не пойду в бассейн."))
    print(preprocess_text("Я уважаю и люблю вас, потому что вы мои маленькие хомячки"))
