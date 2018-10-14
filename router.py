# coding=utf-8
import select, socket, sys, json, threading, time, struct

def routeMessage(source, destinaton, typeT, payload):
	outMessage = {
		"source": source,
		"destination": destination,
		"type": typeT,
		"payload":payload										
	}
	return json.dumps(outMessage)

def routeMessage(source, destinaton, typeT):
	outMessage = {
		"source": source,
		"destination": destination,
		"type": typeT											
	}		

def addEnlace(ip, weight, enlaces, addr):
	# enlaces[toWhere][gateway]
	if(not ip in enlaces):
		enlaces[ip] = {}
	enlaces[ip][addr] = weight
	print('==== Enlaces ====')
	print(enlaces)

def delEnlace(ip, enlaces, addr):
	if(ip in enlaces):
		if(addr in enlaces[ip]):
			del enlaces[ip][addr]
			print("Removed ip ", ip)		

def getValidRoutes(enlaces, currentIp):
	# Split Horizon
	validRoutes = {}
	for key, value in enlaces.items():
		for gateway, value in enlaces[key].items():
			if(key != currentIp and gateway != currentIp and (not key in validRoutes or value < validRoutes[key])):
				validRoutes[key] = value
	return validRoutes

def receiveUpdate():
	return 0		

def sendUpdate(addr, period, enlaces, PORT, udp):
	while(True):
		time.sleep(period)
		# print('Updating')
		for key, value in enlaces.items():
			validRoutes = getValidRoutes(enlaces, key)
			updateMessage = {
				'type': 'update',
				'source': addr,
				'destination': key,
				'distances': validRoutes
			}
			print(validRoutes)
			updateMessage = json.dumps(updateMessage)
			udp.sendto(updateMessage.encode('latin1'), (key, PORT))
			print('Sent update')

def main(addr, period, startup):
	udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	PORT = 55151
	udp.bind((addr, PORT))
	enlaces = {}
	
	sendUpdateThread = threading.Thread(target=sendUpdate, args=(addr, period, enlaces, PORT, udp))
	sendUpdateThread.start()

	while(True):
		command = input().lower().split(' ')

		if(command[0] == 'add'):
			if(len(command) >= 3):
				addEnlace(command[1], command[2], enlaces, addr)
			else:
				print('Invalid params, add should have an ip and weight.')
		elif(command[0] == 'del'):
			if(len(command) >= 2):
				delEnlace(command[1], enlaces)
			else:
				print('Invalid params, del should have an ip')
		elif(command[0] == 'trace'):
			print('Should thrace')
		elif(command[0] == 'quit'):
			exit(1)
		else:
			print('Invalid command, please try again.')

if __name__ == "__main__":
	main(sys.argv[1], int(sys.argv[2]), len(sys.argv) == 4 and sys.argv[3])
