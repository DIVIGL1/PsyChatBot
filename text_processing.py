# Необходимо один зар загрузить корпус стоп слов,
# то есть надо раскомментировать две следующие троки.

# import nltk
# nltk.download("stopwords")

from nltk.corpus import stopwords
from pymystem3 import Mystem
from string import punctuation

mystem = Mystem()
russian_stopwords = set(stopwords.words("russian")) ^ {"не", "нет"}
# russian_stopwords = stopwords.words("russian")


def preprocess_text(text):
    tokens = mystem.lemmatize(text.lower())
    tokens = [token for token in tokens if token not in russian_stopwords \
              and token != " " \
              and token.strip() not in punctuation]

    text = " ".join(tokens)

    return text


if __name__ == '__main__':
    print(preprocess_text("Сегодня я не пойду в бассейн."))
    print(preprocess_text("Я уважаю и люблю вас, потому что вы мои маленькие хомячки"))
