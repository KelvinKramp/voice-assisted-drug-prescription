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
    "The patient medication list now consists of  {medication_list} and I am going to add {new_drug} \
    in a dosing of {dosing}mg {numb_day} times per day. Is this ok?",
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
    # define human voice input as string1
    string1 = voice_input
    # make drug_name a global variable because we need to use them outside the function
    global drug_name
    # start a for loop to parse the medication dictionary
    for drug_name in medication_dictionary:
        # define drug in dictionary as string2
        string2 = drug_name
        # calculate Levenshtein distance between the drug name and the different words in the input string
        partial_ratio = fuzz.partial_ratio(string1.lower(), string2.lower())
        if partial_ratio > 80:
            print("found medication in list: ", drug_name, ", partial ratio = ", partial_ratio)
            # make numb (number of times per day and dose global variable, we need to use them outside the function
            global numb, dose
            # define numb as first item of list in the value of dictionary key (drug)
            numb = medication_dictionary.get(string2)[0]
            # define numb as second item of list in the value of dictionary key (drug)
            dose = medication_dictionary.get(string2)[1]
            if string2.lower() == "augmentin":
                numb = adjust_dose_augm(numb)
                text_speech(conversation_list[2].format(medication=drug_name, numb_day=numb, dosing=dose, GFR=GFR,
                                                        weight=weight))  # speak!
                return
            else:
                text_speech(conversation_list[1].format(medication=drug_name, numb_day=numb, dosing=dose))  # speak!
                return
    # let voice assistant say there was an error if drug was not found
    text_speech(conversation_list[-1])
    # let user give new input in case of error
    voice_input = speech_text()
    # go into loop (start function again) in the case of no match
    get_standard_dose(voice_input)


import os
import sys

def decision(voice_input):
    # approval
    if str.lower(voice_input) == "yes":
        return
    # change
    if str.lower(voice_input) == "no":
        text_speech(conversation_list[3])
        voice_input = speech_text()
        # confirm change
        if "change" in str.lower(voice_input):
            text_speech(conversation_list[4])
            # input number of mg
            global dose
            dose = speech_text()
            print(dose)
            text_speech(conversation_list[5])
            # input times per day
            global numb
            numb = speech_text()
            print(numb)
            # closed loop communication
            text_speech(conversation_list[6].format(dosing=dose, numb_day=numb))
            voice_input = speech_text()
            # if new dosing correct continue
            if str.lower(voice_input) == "yes":
                return
            # new dosing incorrect restart function
            if str.lower(voice_input) == "no":
                decision(voice_input)
    # cancel
    if str.lower(voice_input) == "cancel":
        #  restart script
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

# check if drug in medication list
if drug_name in download_medication_list:
    text_speech("The drug is already in the medication list.")
else:
    # closed loop communication
    text_speech(conversation_list[9].format(medication_list=download_medication_list, new_drug=drug_name,
                                            numb_day=numb, dosing=dose))
    voice_input = speech_text()
    if "yes" in voice_input.lower():
        pass
    else:
        text_speech(conversation_list[7])
        os.execv(sys.executable, ['python'] + sys.argv)
    # prescribe new medication
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

# print list
for item in adjusted_medication_list:
    print(item)

# close browser
driver.close()
