import httpx
import os

APP_TOKEN = None


def api_token():
  global APP_TOKEN
  try:
    with httpx.Client(timeout=5) as client:
      post_data = {
          "application_id": os.environ['cfID'],
          "secret": os.environ['cfSecret'],
      }
      response = client.post("https://data.cftools.cloud" +
                             "/v1/auth/register",
                             json=post_data)
      response.raise_for_status()
      APP_TOKEN = response.json()["token"]
      return APP_TOKEN
  except Exception as e:
    print(f"Error retrieving API Token: {e}")


def check_ban(cftools_id):
  try:
    with httpx.Client(timeout=5) as client:
      headers = {"Authorization": f"Bearer {APP_TOKEN}"}
      params = {"filter": cftools_id}
      response = client.get(
          f"https://data.cftools.cloud/v1/banlist/62ca0d4fd5df6a4a8d63e911/bans",
          headers=headers,
          params=params)
      data = response.json()
      return data
  except Exception as e:
    print(f"Error checking ban status: {e}")

def check_cheating(cftools_id):
  data = check_ban(cftools_id)
  if data and 'entries' in data:
      for entry in data['entries']:
          reason = entry.get('reason', '')
          if 'cheat' in reason.lower():
              return True
  return False

def get_players(serverID):
  try:
    with httpx.Client(timeout=5) as client:
      headers = {"Authorization": f"Bearer {APP_TOKEN}"}
      response = client.get(
          f"https://data.cftools.cloud/v1/server/{serverID}/GSM/list",
          headers=headers,
      )
      data = response.json()

      cftools_ids = []
      steamIDs = []
      for session in data["sessions"]:
        cftools_ids.append(session["gamedata"]["steam64"])
        info = {
          "steam64": session["gamedata"]["steam64"],
          "name": session["gamedata"]["player_name"],
        }
        steamIDs.append(info)
        #steamIDs.append(session["steam_id"])
      info = [cftools_ids, steamIDs]
      return info
  except Exception as e:
    print(f"Error retrieving list of players: {e}")


class CFtools:
  #Constructor for cftools class to make it easier to request data from API. Sets
  def __init__(self, cftoolsID, serverID, APP_TOKEN):
  
    self.cftoolsID = cftoolsID
    self.baseURL = "https://data.cftools.cloud"
    self.API_TIMEOUT = 5
    self.serverID = serverID
    self.APP_TOKEN = APP_TOKEN
  
    self.steamID = None
    self.hitStats = None
    self.name = None
  
    #Hit Stats self saving
  
    self.head = 0
    self.torso = 0
    self.leftArm = 0
    self.rightArm = 0
    self.leftLeg = 0
    self.rightLeg = 0
    self.kd = 0
    self.playtime = 0
  
  #
  def get_profile_info(self):
    try:
      with httpx.Client(timeout=self.API_TIMEOUT) as client:
        headers = {"Authorization": f"Bearer {self.APP_TOKEN}"}
        get_params = {"cftools_id": self.cftoolsID}
        response = client.get(
            f"{self.baseURL}/v2/server/{self.serverID}/player",
            params=get_params,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        self.steamID = data["identities"]["steam"]["steam64"]
        self.kd = str(
            data.get(self.cftoolsID,
                     {}).get('game', {}).get('dayz', {}).get('kdratio', 0))
        kills = data.get(self.cftoolsID,
                         {}).get('game', {}).get('dayz',
                                                 {}).get('kills',
                                                         {}).get('players', 0)
  
        weapon_data = data.get(self.cftoolsID,
                               {}).get("game", {}).get("dayz",
                                                       {}).get("weapons", {})
  
        self.playtime = data.get(self.cftoolsID, {}).get('omega', {}).get(
            'playtime', 0) / 3600
        name_history = data.get(self.cftoolsID,
                                {}).get('omega', {}).get('name_history', [])
  
        if int(kills) < -5:
          print("Kill threshhold not met")
        else:
          try:
            hit_zones = [
                'head', 'torso', 'leftarm', 'rightarm', 'leftleg', 'rightleg'
            ]
            guns_to_exclude = [
                'm9a1_bayonet_northmen', 'baseballbat', 'm9a1_bayonet_nonvip',
                'flag_napa', 'tacticalbaconcan_opened', 'woodaxe',
                'sledgehammer', "mp133shotgun",  "m9a1_bayonet_nonvip", "bandagedressing",
                "fieldshovel"
            ]
            total_hits = {zone: 0 for zone in hit_zones}
            hit_zone_exists = False
            for weapon_name, weapon_stats in weapon_data.items():
              if weapon_name in guns_to_exclude:
                continue
              zones = weapon_stats.get('zones', {})
              if any(zones.get(zone) is not None for zone in hit_zones):
                hit_zone_exists = True
              for zone in hit_zones:
                if zone == "head":
                  # Combine "brain" zone hits with "head" zone hits
                  total_hits["head"] += zones.get("brain", 0) + zones.get(
                      "head", 0)
                else:
                  total_hits[zone] += zones.get(zone, 0)
  
            total_count = sum(total_hits.values())
            if (total_count == 0):
              total_count = 1
            percentages = {
                zone: round((hits / total_count) * 100, 2)
                for zone, hits in total_hits.items()
            }
            self.head = percentages["head"]
            self.torso = percentages["torso"]
            self.leftArm = percentages["leftarm"]
            self.rightArm = percentages["rightarm"]
            self.leftLeg = percentages["leftleg"]
            self.rightLeg = percentages["rightleg"]
  
            message = f"{self.kd}," + f"{self.playtime}," + ",".join(
                [str(percentage) for percentage in percentages.values()])
            if name_history:
              self.name = name_history[-1].strip()
            else:
              self.name = None
            if message is not None:
              self.hitStats = message
            return message
          except Exception as e:
            print(f"Error retrieving hitzones: {e}")
    except Exception as e:
      print(f"Error retrieving profile info: {e}")
  