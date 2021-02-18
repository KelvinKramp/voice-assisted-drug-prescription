import speech_recognition as sr
import pyttsx3

#brew install portaudio
#pip install pyaudio
# https://stackoverflow.com/questions/33851379/pyaudio-installation-on-mac-python-3
# xcode-select --install
# brew remove portaudio
# brew install portaudio
# pip3 install pyaudio

conversation_list = [
    "How can I help you?...",
    "You want to start with {medication}. \
    The standard dosing is {numb_day} times a day {dosing}mg. Is this what you want to prescribe?",
    "Based on a kidneyfunction of {GFR} and a weight of {weight} kg, \
    I calculated a needed dosing of {numb_day} times a day {dosing}mg. Is this what you want to prescribe?",
    "Do you want to change the dose or cancel prescription?",
    "How much milligram do you want to prescribe?",
    "How many times per day do you want the patient to take this?",
    "Ok, do you want to change the dosing to {dosing}mg {numb_day} times per day?",
    "Ok, let's start over again",
    "Ok, I will prescribe {medication} in a dosis of {dosing}",
    "The patient medication list now consists of  {medication_list}",
    "I didn't hear you correctly, or the drug is not in my drug dictionary, please tell me again which drug you want \
    to prescribe"]


def text_speech(text_line):
    engine = pyttsx3.init()  # import the pyttsx3 module functions under the name engine
    engine.say(text_line)  # prime the say function with the variable text_line
    engine.runAndWait()  # run the tts function, without calling this function the voice assistant doesnt start talking

def speech_text():
    r = sr.Recognizer()
    # start capturing audio from microphone
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)
    # analyse speech using google speech tot text
    try:
        string = r.recognize_google(audio)
        print(string)
    except Exception as e:
        print(e)
        string = "error occured during NLP of audio"
    # return result as string
    return string


medication_dictionary = {
    "Morphine": [6,5],
    "Midazolam":  [6,5],
    "Metoprolol": [1,50],
    "Ciproxine": [2,500],
    "Augmentin": [3,625],
    "Amoxicillin": [3,500],
}

# import scraping modules
from selenium import webdriver
import pandas as pd

# open browser
driver = webdriver.Chrome()

# scrape lab results
driver.get("https://medicalprogress.dev/patient_file2/lab_results.html")
html = driver.page_source
data = pd.read_html(html)

# clean the data
data = data[0]
df = pd.DataFrame(data)

# extract GFR
GFR = df.iloc[2,1]

# scrape weight
driver.get("https://medicalprogress.dev/patient_file2/weight.html")
html = driver.page_source
data = pd.read_html(html)

# clean the data
data = data[0]
df = pd.DataFrame(data)

# extract weight
weight = df.iloc[3,1]


# Adjust augmentin dose function
def adjust_dose_augm(numb):
    print(weight,GFR)
    if weight < 40:
        raise Exception(text_speech("I received an error, the weight is lower than 40kg"))
    if 30 > GFR > 10:
        numb = 2
    if GFR < 10:
        numb = 1
    return numb


from fuzzywuzzy import fuzz

# get standard dose function
def get_standard_dose(voice_input):
    string1 = voice_input  # define human voice input as string1
    global drug_name # make drug_name a global variable because we need to use them outside the function
    for drug_name in medication_dictionary:  # start a for loop to parse the medication dictionary
        string2 = drug_name # define drug in dictionary as string2
        # calculat Levenshtein distance between the drug name and the different words in the input string
        partial_ratio = fuzz.partial_ratio(string1.lower(), string2.lower())
        if partial_ratio > 80:
            print("found medication in list: ", drug_name, ", partial ratio = ", partial_ratio)
            global numb, dose  # make numb (number of times per day and dose global variable, we need to use them outside the function
            numb = medication_dictionary.get(string2)[0]  # define dose as dose (first value) within the dictionary key (drug)
            dose = medication_dictionary.get(string2)[1]  # define dose as dose (second value) within the dictionary key (drug)
            text_speech(conversation_list[1].format(medication=drug_name, numb_day=numb, dosing=dose))  # speak!
            if string2 == "Augmentin":
                numb = adjust_dose_augm(numb)
                text_speech(
                    conversation_list[2].format(medication=drug_name, numb_day=numb, dosing=dose, GFR=GFR,
                                                weight=weight))  # speak!
                return
            else:
                text_speech(conversation_list[1].format(medication=drug_name, numb_day=numb, dosing=dose))  # speak!
                return
    text_speech(conversation_list[-1]) # let voice assistant say there was an error
    voice_input = speech_text() # let user give new input
    get_standard_dose(voice_input) # go into loop (start function again) in the case of no match


import os
import sys

def decision(voice_input):
    if str.lower(voice_input) == "yes": # approval
        return
    if str.lower(voice_input) == "no": # change
        text_speech(conversation_list[3])
        voice_input = speech_text()
        if "change" in str.lower(voice_input): # confirm change
            text_speech(conversation_list[4])
            global dose
            dose = speech_text()
            print(dose)
            text_speech(conversation_list[5])
            global numb
            numb = speech_text()
            print(numb)
            text_speech(conversation_list[6].format(dosing = dose, numb_day=numb))
            voice_input = speech_text()
            if str.lower(voice_input) == "yes": # new dosing correct
                return
            if str.lower(voice_input) == "no": # new dosing incorrect
                decision(voice_input) # loop again to change in the workflow if the new dose is incorrect
    if str.lower(voice_input) == "cancel": # cancel prescription and restart script
        os.execv(sys.executable, ['python'] + sys.argv)


text_speech(conversation_list[0])
voice_input = speech_text()
get_standard_dose(voice_input)
voice_input = speech_text()
decision(voice_input)


# pip install html5lib, pip install beautifulsoup4
from bs4 import BeautifulSoup

driver.get("https://medicalprogress.dev/patient_file2/medication_list.html")
html = driver.page_source
soup = BeautifulSoup(html, 'lxml')

download_medication_list = []
for li in soup.findAll('li'):
    download_medication_list.append(li.getText())

import time

if drug_name in download_medication_list:
    text_speech("The drug is already in the medication list.")
else:
    time.sleep(1)
    input_field = driver.find_element_by_xpath("/html/body/input[1]")
    input_field.send_keys(drug_name + " " + str(dose) + "mg " + str(numb) + " times per day") # fill in info in inputfield
    time.sleep(1)
    driver.find_element_by_xpath("/html/body/input[2]").click() # click on the add button
    time.sleep(1)

# redownload adjusted medication list
time.sleep(2)
html = driver.page_source
soup = BeautifulSoup(html, 'lxml')

# get drugs from adjusted medication list
adjusted_medication_list = []
for li in soup.findAll('li'):
    adjusted_medication_list.append(li.getText())

# speak adjusted medication list outloud
text_speech(conversation_list[9].format(medication_list = str(adjusted_medication_list)))
