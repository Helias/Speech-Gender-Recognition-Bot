from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, RegexHandler, CallbackQueryHandler, Filters
from pydub import AudioSegment
from sklearn.preprocessing import Normalizer
from sklearn.decomposition import PCA

import logging
import numpy as np
import pickle

import subprocess
import os

# get token from token.conf
TOKEN = open("token.conf", "r").read().strip()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# load model
svc = pickle.load(open("models_trained/svc_model.sav", 'rb'))
pca = pickle.load(open("models_trained/pca.sav", 'rb'))
norm = Normalizer(norm='l2')

def start(bot, update):
  update.message.reply_text('Hi! Send me a vocal message and I tell you if you are "male" or "female"!')

def echo(bot, update):
  update.message.reply_text(update.message.text)

def predict(bot, update):
  file_id = update.message.voice.file_id
  new_file = bot.get_file(file_id)
  new_file.download('voice.ogg')

  sound = AudioSegment.from_ogg("voice.ogg")
  sound.export("voice.wav", format="wav")

  FNULL = open(os.devnull, 'w')
  subprocess.call(('Rscript', "R/extract_feature.r"), stdout=FNULL, stderr=subprocess.STDOUT)

  # read second line of csv file (so exclude header)
  sample = open("my_voice.csv", "r").read().split("\n")[1].split(",")
  sample = [sample]

  sample = norm.transform(np.float64(sample))
  sample = pca.transform(np.float64(sample))

  if int(svc.predict(sample)) == 0:
    update.message.reply_text("You are male!")
  else:
    update.message.reply_text("You are female!")

def main():
  updater = Updater(TOKEN)

  dp = updater.dispatcher

  dp.add_handler(MessageHandler(Filters.voice, predict))
  dp.add_handler(CommandHandler('start', start))
  dp.add_handler(CommandHandler('help', start))

  updater.start_polling()
  updater.idle()


if __name__ == '__main__':
  main()
