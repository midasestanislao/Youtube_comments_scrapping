import time
import csv
import pandas as pd
from selenium.webdriver import Chrome
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from string import punctuation
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer, LancasterStemmer
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re
import nltk
nltk.downloader.download('vader_lexicon')

# Guardar en CSV
with open("/mnt/c/Users/leoni/Desktop/Proyecto_webScrapping_twitter/tweets.csv", "w", newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Tweet_count", "Username", "Text", "Created At", "Retweets", "Likes"])


def process_youtube_comments(youtube_video_url, category):
    data = []
    user = []
    timer = []

    chromedriver_autoinstaller.install()
    with Chrome() as driver:
        wait = WebDriverWait(driver, 20)
        driver.get(youtube_video_url)

        for item in range(4):  # By increasing the highest range you can get more content
            wait.until(EC.visibility_of_element_located((By.TAG_NAME, "body"))).send_keys(Keys.END)
            time.sleep(3)

        for comment in wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#comment #content-text"))):
            data.append(comment.text)

        for author in wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#header-author #author-text"))):
            user.append(author.text)

        for times in wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#header-author #published-time-text"))):
            timer.append(times.text)

    df = pd.DataFrame(data, columns=['comment'])
    df_ = pd.DataFrame(user, columns=['author'])
    df_time = pd.DataFrame(timer, columns=['time'])
    
    # Combine the dataframes
    combined_df = pd.concat([df, df_, df_time], axis=1).dropna()
    
    # Language settings
    idioma = "english"
    stop_words = stopwords.words(idioma)
    porter_stemmer = PorterStemmer()
    lancaster_stemmer = LancasterStemmer()
    snowball_stemmer = SnowballStemmer(language=idioma)
    lzr = WordNetLemmatizer()

    def text_processing(text):
        # Convierte todo en string
        text = str(text)
        
        # Conver text in lower
        text = text.lower()

        # remove new line characters in text
        text = re.sub(r'\n',' ', text)
        
        # remove punctuations from text
        text = re.sub('[%s]' % re.escape(punctuation), "", text)
        
        # remove references and hashtags from text
        text = re.sub("^a-zA-Z0-9$,.", "", text)
        
        # remove multiple spaces from text
        text = re.sub(r'\s+', ' ', text, flags=re.I)
        
        # remove special characters from text
        text = re.sub(r'\W', ' ', text)

        text = ' '.join([word for word in word_tokenize(text) if word not in stop_words])
        
        # lemmatizer using WordNetLemmatizer from nltk package
        text = ' '.join([lzr.lemmatize(word) for word in word_tokenize(text)])

        return text


    combined_df['comment'] = combined_df['comment'].apply(text_processing)

    # Sentiment analysis
    sentiment = SentimentIntensityAnalyzer()
    combined_df["Positive"] = [sentiment.polarity_scores(i)["pos"] for i in combined_df['comment']]
    combined_df["Negative"] = [sentiment.polarity_scores(i)["neg"] for i in combined_df['comment']]
    combined_df["Neutral"] = [sentiment.polarity_scores(i)["neu"] for i in combined_df['comment']]
    combined_df["Compound"] = [sentiment.polarity_scores(i)["compound"] for i in combined_df['comment']]

    neg = combined_df["Negative"].values
    pos = combined_df["Positive"].values

    # Determinar el sentimiento basado en las puntuaciones de negativo y positivo
    sentiments = []
    for n, p in zip(neg, pos):
        if n > p:
            sentiments.append('Negative')
        elif p > n:
            sentiments.append('Positive')
        else:
            sentiments.append('Neutral')

    combined_df["Sentiment"] = sentiments
    
    #Filtrado por categoria
    filtered_df = combined_df[combined_df["comment"].str.contains("|".join(category))]
    
    
    Pos_filtered_df = combined_df[combined_df['Sentiment'] == 'Positive']
    # Neg_filtered_df = combined_df[combined_df['Sentiment'] == 'Negative']
    Pos_filtered_df = Pos_filtered_df.drop(columns=["Positive", "Negative", "Neutral", "Compound"])
    # Neg_filtered_df = Neg_filtered_df.drop(columns=["Positive", "Negative", "Neutral", "Compound"])

    # Seleccion del tipo de comentario
    filtered_df = Pos_filtered_df
    filtered_df.to_csv('/mnt/c/Users/leoni/Desktop/Proyecto_webScrapping_youtube/comments.csv', index=False)

    return filtered_df

# Uso de la función
# Liga del video
youtube_video_url = "https://www.youtube.com/watch?v=hmL8al8twIE"

# Palabras para buscar
# category = ['trump', 'kamala', 'president', 'united states', 'elections', 'usa', 'winner', 'loser']
category = ['kamala', 'president', 'united states', 'elections', 'usa', 'winner', 'woman']
# Se puede priorizar los comentarios con la variable de categoria

# Proceso de filtraccion
filtered_df = process_youtube_comments(youtube_video_url, category)

print(filtered_df)