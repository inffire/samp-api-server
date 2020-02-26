import json
import time
import random
import falcon

user_list = {
	"3bfc192b2ca695f916b1aba0c2c94444": {"name": "bot1", "lastupdate": 0},
	"41ddb68db6b861db5b69073944d1e704": {"name": "bot2", "lastupdate": 0},
	"95fb566dbf89545a55ae927f0f4afea2": {"name": "bot3", "lastupdate": 0}
}

def timestamp():
	return int(time.time() * 1000.0)


class AuthMiddleware(object):
	def process_request(self, req, resp):
		token = req.get_param("token", False)
		if token is None:
			raise falcon.HTTPUnauthorized()
		if not token in user_list:
			raise falcon.HTTPUnauthorized()


class Message():
	def __init__(self):
		self.from_player = ""
		self.to_player = ""
		self.text = ""
		self.timestamp = 0
		
	def payload(self):
		return {
				"type": "Message",
				"from": self.from_player,
				"timestamp": self.timestamp,
				"payload":
				{
					"text": self.text
				}
			}


class Player():
	def __init__(self):
		self.from_player = ""
		self.id = 65535
		self.x = 0
		self.y = 0
		self.z = 0
		self.color = 0xff0000ff
		self.timestamp = 0
		
	def __eq__(self, other):
		"""Overrides the default implementation"""
		if isinstance(other, Player):
			return self.id == other.id
		return False
		
	def payload(self):
		return {
				"type": "Player",
				"from": self.from_player,
				"timestamp": self.timestamp,
				"payload":
				{
					"id": self.id,
					"x": self.x,
					"y": self.y,
					"z": self.z,
					"color": self.color
				}
			}


class MapTarget():
	def __init__(self):
		self.from_player = ""
		self.x = 0
		self.y = 0
		self.timestamp = 0
		
	def payload(self):
		return {
				"type": "MapTarget",
				"from": self.from_player,
				"timestamp": self.timestamp,
				"payload":
				{
					"x": self.x,
					"y": self.y
				}
			}


class UserResource():
	def on_get(self, req, resp):
		token = req.get_param("token", True)
		user_lastupdate = user_list[token]["lastupdate"]
		print("[{}] getUpdates() {}".format(time.strftime("%x %X"), token))
		
		global updateQueue
		data = [item.payload() for item in updateQueue if item.timestamp >= user_lastupdate]
		
		# autoclean queue
		updateQueue = [item for item in updateQueue if timestamp() - item.timestamp < 10000]
		print("[{}] updateQueue:".format(time.strftime("%x %X")), updateQueue)

		user_list[token]["lastupdate"] = timestamp()
		resp.body = json.dumps( {"response": data} )


class onPlayerMessage():
	def __init__(self):
		pass
		
	def on_post(self, req, resp):
		token = req.get_param("token", required=True)
		try:
			text = req.media["text"]
			tmp_message = Message()
			tmp_message.from_player = user_list[token]["name"]
			tmp_message.text = text
			if len(text) > 96:
				raise ValueError("len(req.media[\"text\"])={}".format(len(text)))
			tmp_message.timestamp = timestamp()
			updateQueue.append(tmp_message)
		except Exception as e:
			print("[{}] {}: {}".format(time.strftime("%x %X"), token, e))
			raise falcon.HTTPBadRequest()


class onPlayer():
	def __init__(self):
		pass
		
	def on_post(self, req, resp):
		token = req.get_param("token", required=True)
		try:
			tmp_player = Player()
			tmp_player.from_player = user_list[token]["name"]
			
			tmp_player.id = int(req.media["id"])
			if not tmp_player.id in range(0, 1000):
				raise ValueError("tmp_player.id={}".format(tmp_player.id))
				
			tmp_player.x = float(req.media["x"])
			if not -6000.0 < tmp_player.x < 6000.0:
				raise ValueError("tmp_player.x={}".format(tmp_player.x))
				
			tmp_player.y = float(req.media["y"])
			if not -6000.0 < tmp_player.y < 6000.0:
				raise ValueError("tmp_player.y={}".format(tmp_player.y))
				
			tmp_player.z = float(req.media["z"])
			if not -1000.0 < tmp_player.z < 6000.0:
				raise ValueError("tmp_player.z={}".format(tmp_player.z))
				
			tmp_player.color = int(req.media["color"])
			tmp_player.color = tmp_player.color & 0xffffff00
			tmp_player.color = tmp_player.color | 0xff
			
			tmp_player.timestamp = timestamp()
			
			for item in updateQueue:
				if item == tmp_player:
					item.__dict__ = tmp_player.__dict__
					item.timestamp = tmp_player.timestamp
					break
			else:
				updateQueue.append(tmp_player)
				
		except Exception as e:
			print("[{}] {}: {}".format(time.strftime("%x %X"), token, e))
			raise falcon.HTTPBadRequest()


class onMapTarget():
	def __init__(self):
		pass
		
	def on_post(self, req, resp):
		token = req.get_param("token", required=True)
		try:
			tmp_target = MapTarget()
			tmp_target.from_player = user_list[token]["name"]
			
			tmp_target.x = float(req.media["x"])
			if not -6000.0 < tmp_target.x < 6000.0:
				raise ValueError("tmp_target.x={}".format(tmp_target.x))
				
			tmp_target.y = float(req.media["y"])
			if not -6000.0 < tmp_target.y < 6000.0:
				raise ValueError("tmp_target.y={}".format(tmp_target.y))
				
			tmp_target.timestamp = timestamp()
			updateQueue.append(tmp_target)
		except Exception as e:
			print("[{}] {}: {}".format(time.strftime("%x %X"), token, e))
			raise falcon.HTTPBadRequest()


api = falcon.API(middleware=[
	AuthMiddleware()
])

updateQueue = []

users = UserResource()

messageHandler 	= onPlayerMessage()
playerHandler 	= onPlayer()
targetHandler 	= onMapTarget()
api.add_route('/api/v1/sendMessage', messageHandler)
api.add_route('/api/v1/sendPlayer', playerHandler)
api.add_route('/api/v1/sendTarget', targetHandler)

api.add_route('/api/v1/getUpdates', users)
