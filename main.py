from logging import exception
from discord import message, webhook
from discord.webhook.async_ import Webhook
from flask import Flask, request, jsonify
import hashlib
import os
import warnings
import cftools as cf
from cftools import CFtools
from Argus.model import Model
import dbHelper
from datetime import datetime
import asyncio
import requests
import json
import discord
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# Your Discord webhook URL
def post_to_discord(cf,WEBHOOK_URL):
  headers = {'Content-Type': 'application/json'}
  payload = {'content': f"Player {cf} has been banned for cheating"}
  try:
    response = requests.post(WEBHOOK_URL,
                             headers=headers,
                             data=json.dumps(payload))
    if response.status_code == 204:
      print("Webhook sent successfully!")
    else:
      print(f"Failed to send webhook. Status code: {response.status_code}")
  except Exception as e:
    print(f"An error occurred: {e}")


@app.route("/", methods=["GET"])
def route():
  return "", 200


@app.route("/getTable", methods=["GET"])
def get_table():
  start_date = request.args.get(
      'start_date')  # Get the start_date from the URL parameters
  db_name = request.args.get(
      'server_name')  # Get the table_name from the URL parameters
  if not start_date:
    return jsonify({'error': 'Start date parameter is required.'}), 400

  data = dbHelper.get_entries_between_dates(start_date, db_name)
  return jsonify(data), 200


@app.route('/callTrigger', methods=['POST'])
async def callTrigger():
  try:
    event_type = request.headers.get('X-Hephaistos-Event')
    uuid = request.headers.get("X-Hephaistos-Delivery")
    db_name =request.args.get("server_name")
    secret = os.environ[db_name] # type: ignore
    if event_type == "verification":
      return '', 204

    #Verifies authenticity of webhook by hasing uuid and secret then checking if match with cftools signature.
    if not hashlib.sha256(f"{uuid}{secret}".encode(
        'utf-8')).hexdigest() == request.headers.get("X-Hephaistos-Signature"):
      raise Exception("Signature Mismatch!")
    data = request.get_json()
    killer_cf = data["murderer_id"]
    ID = os.environ[f"server_{db_name}"]
    #creating CFTools object
    player = CFtools(cftoolsID=killer_cf,
                     serverID=ID,
                     APP_TOKEN=cf.api_token())
    player.get_profile_info()
    date = datetime.now().strftime("%d/%m/%Y")
    if (player.hitStats is not None):
      prediction = Model(player.hitStats)
      prediction.scan()
      db_save_data = {
          "steam_id": player.steamID,
          "cfid": player.cftoolsID,
          "date": date,
          "name": player.name,
          "prediction": f"{prediction.prediction}",
          "hitStats": player.hitStats,
          "hitzones": {
              "head": player.head,
              "torso": player.torso,
              "leftArm": player.leftArm,
              "rightArm": player.rightArm,
              "leftLeg": player.leftLeg,
              "rightLeg": player.rightLeg,
          },
          "others": {
              "kd": player.kd,
              "playtime": player.playtime
          }
      }
      dbHelper.add_user(db_save_data, table_name=db_name)
      if prediction.prediction == "0":
        print("Posting to discord!")
        post_to_discord(
            cf=killer_cf,
            WEBHOOK_URL=
            "https://discord.com/api/webhooks/1114405051482513489/t3fuzsx0iU5xCcp8xkl16WBxhvt9IiZsK1EZsh6kGxUmUaOplKWpaifg1cepZB540tJ8"
        )
      else:
        post_to_discord(
            cf=killer_cf,
            WEBHOOK_URL=
            "https://discord.com/api/webhooks/1114405146319913070/R5hyOy57iFfPqQAM6aBB8w_1ShkP5U13pzVNFIL8BdwagBlVAc_PmrDsQxHt32rwuURL"
        )

    else:
      warnings.warn(f"{player.name}'s prediction: None")
    return "Executed Successfully", 200
  except Exception as e:
    post_to_discord(
        cf=e,
        WEBHOOK_URL=
        "https://discord.com/api/webhooks/1114405051482513489/t3fuzsx0iU5xCcp8xkl16WBxhvt9IiZsK1EZsh6kGxUmUaOplKWpaifg1cepZB540tJ8"
    )
    return f'Error: {e}', 510


@app.route('/getCurrent', methods=['GET'])
def getCurrent():
    try:
        server_id = request.args.get('server_identifier')
        db_name = request.args.get('server_name')
        cf.api_token()
        info = cf.get_players(server_id)[1] # type: ignore
        steam_ids = [player['steam64'] for player in info]
        player_data = dbHelper.getBulkData(steam_ids, db_name=db_name) # type: ignore
        data = []
        counter = 0
        for player in info:
            playerInfo = player_data[counter]
            if playerInfo is not None:
                cheater = False
                for entry in playerInfo:
                    if entry.get("prediction") == "0":
                        cheater = True
                        data.append(entry)
                        break
                if not cheater:
                    data.append(playerInfo[-1])
            else:
                returnState = {
                    "steam64": player["steam64"],
                    "prediction": "None",
                    "name": player["name"],
                }
                data.append(returnState)
            counter = counter +1
        return jsonify(data), 200
    except Exception as e:
        return jsonify(e), 510
        


app.run(host='0.0.0.0', port=8080)