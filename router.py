# coding=utf-8
import select, socket, sys, json, threading, time, struct
from random import randint

# ip addr add 127.0.1.6/32 dev lo
# add 127.0.1.4 10
# add 127.0.1.5 10

# ip addr add 127.0.1.4/32 dev lo
# add 127.0.1.1 15
# add 127.0.1.2 15
# add 127.0.1.3 5
# add 127.0.1.5 15

# ip addr add 127.0.1.5/32 dev lo
# add 127.0.1.1 20
# add 127.0.1.2 20
# add 127.0.1.3 10

def selectRoute(gateway):
	return gateway[randint(0,len(gateway)-1)]


def routeMessage(source, destinaton, typeT, payload):
	outMessage = {
		"source": source,
		"destination": destination,
		"type": typeT,
		"payload":payload										
	}
	return json.dumps(outMessage)

def addEnlace(ip, weight, enlaces, addr, lastUpdates):
	# enlaces[toWhere][gateway]
	if(not ip in enlaces):
		enlaces[ip] = {}
	enlaces[ip][addr] = weight
	lastUpdates[ip] = time.time()
	print('==== Enlaces ====')
	print(enlaces)

def delEnlace(ip, enlaces, addr):
	if(ip in enlaces):
		if(addr in enlaces[ip]):
			del enlaces[ip][addr]
		if(len(enlaces[ip]) == 0):
			del enlaces[ip]
			for currentGate in list(enlaces):
				if ip in list(enlaces[currentGate]):
					del enlaces[currentGate][ip]
					if len(enlaces[currentGate]) == 0:
						del enlaces[currentGate]
	 
	print('==== Enlaces after remove ====')
	print(enlaces)

def addRouteToTraceMessage(message, currentIp):
	return 0		

def getShortestPath(enlaces, ip, addr):
	smallerDistance = sys.maxsize
	gateway = []
	if(ip in enlaces):
		for neighborhood in enlaces[ip]:
			if int(enlaces[ip][neighborhood]) <= smallerDistance:
				if not smallerDistance == int(enlaces[ip][neighborhood]): gateway = []
				smallerDistance = int(enlaces[ip][neighborhood])
				if(neighborhood == addr):
					gateway.append(ip)
				else:
					gateway.append(neighborhood)
	if(len(gateway) > 1):
		gateway = selectRoute(gateway)
	return [smallerDistance, gateway]

def updateDistances(enlaces, ipRouter, smallestDistanceToUpdatedNode, newSmallestDistanceToUpdatedNode):
	for ip in enlaces:
		for gateway in enlaces[ip]:
			if(gateway == ipRouter):
				enlaces[ip][gateway] += newSmallestDistanceToUpdatedNode - smallestDistanceToUpdatedNode

def fowardMessage(message, ip, enlaces, udp, PORT, addr):
	stringMessage = json.dumps(message)
	print(enlaces)
	nextPath = getShortestPath(enlaces, ip, addr)[1]
	if(nextPath):
		print('\nsending message to', nextPath)
		print('destination', ip)
		print('\n\n')
		udp.sendto(stringMessage.encode('latin1'), (nextPath, PORT))

def receivedUpdate(message, enlaces, lastUpdates, addr):
	# Existe caminho para esse roteador? Se sim, posso adicionar os caminhos dele
	#print('\n\n\n ======= RECEIVING ========')
	## print(message)
	#print('\n')
	if(message['source'] in enlaces):
		lastUpdates[message['source']] = time.time()
		shortestDistanceToGateway = getShortestPath(enlaces, message['source'], addr)[0]
		# Para todos os ips
		for ip in list(enlaces):
			# Calculamos a menor distancia para este ip
			shortestDistanceToIp = getShortestPath(enlaces, ip, addr)[0]
			# Atualizamos ou deletamos se ele não estiver na mensagem
			if(ip in message['distances']):
				enlaces[ip][message['source']] = int(message['distances'][ip]) + shortestDistanceToGateway

			if(message['source'] in list(enlaces[ip]) and not ip in message['distances']):
				delEnlace(ip, enlaces, message['source'])
			
			newShortestDistanceToIp = getShortestPath(enlaces, ip, addr)[0]
			# A menor distancia mudou? Se sim devemos atualizar todos os nós
			if(not newShortestDistanceToIp == shortestDistanceToIp):
				#print('Should update distances')
				updateDistances(enlaces, ip, shortestDistanceToIp, newShortestDistanceToIp)

		# Verificamos se conseguimos alcançar algum novo ip
		for ip in message['distances']:
			if(not ip in enlaces):
				enlaces[ip] = {}
				lastUpdates[ip] = time.time()
				enlaces[ip][message['source']] = int(message['distances'][ip]) + shortestDistanceToGateway
		
		# print(enlaces)
		# print('\n')

def receivedTrace(message, enlaces, addr, udp, PORT):
	message['hops'].append(addr)
	if(message['destination'] == addr):
		dataMessage = { 
			'type': 'data',
			'source': message['destination'],
			'destination': message['source'],
			'payload': json.dumps(message)
		}
		fowardMessage(dataMessage, message['source'], enlaces, udp, PORT, addr)
	else:
		fowardMessage(message, message['destination'], enlaces, udp, PORT, addr)

def receivedData(message, enlaces, addr, udp, PORT):
	if(message['destination'] == addr):
		print(message['payload'])
	else:
		fowardMessage(message, message['destination'], enlaces, udp, PORT, addr)

def receivedMessage(enlaces, lastUpdates, addr, udp, PORT):
	while(True):
		data,address = udp.recvfrom(65536)
		message = json.loads(data.decode('latin1'))
		if(message['type'] == 'update'):
			receivedUpdate(message, enlaces, lastUpdates, addr)
		elif(message['type'] == 'data'):
			receivedData(message, enlaces, addr, udp, PORT)
		elif(message['type'] == 'trace'):
			receivedTrace(message, enlaces, addr, udp, PORT)				
		else:
			print("Tipo de mensagem desconhecido. Tente novamente")

def getValidRoutes(enlaces, currentIp):
	# Split Horizon
	validRoutes = {}
	for key, value in enlaces.items():
		for gateway, value in enlaces[key].items():
			if(key != currentIp and gateway != currentIp and (not key in validRoutes or value < validRoutes[key])):
				validRoutes[key] = value
	return validRoutes

def sendUpdate(addr, period, enlaces, PORT, udp):
	while(True):
		time.sleep(period)
		for key, value in enlaces.items():
			if(addr in value):
				validRoutes = getValidRoutes(enlaces, key)
				updateMessage = {
					'type': 'update',
					'source': addr,
					'destination': key,
					'distances': validRoutes
				}
				updateMessage = json.dumps(updateMessage)
				udp.sendto(updateMessage.encode('latin1'), (key, PORT))

def removeUnusedEnlaces(enlaces, lastUpdates, period):
	while(True):
		currentTime = time.time()
		removeIP = []
		for ip in lastUpdates:
			if(currentTime - lastUpdates[ip] >= 4*period):
				removeIP.append(ip)

		for ip in removeIP:
			print('Deletei enlace', ip)
			del enlaces[ip]
			del lastUpdates[ip]

		for ip in list(enlaces):
			for gateway in list(enlaces[ip]):
				if(gateway in removeIP):
					delEnlace(ip, enlaces, gateway)
					
def sendTrace(destination, source, enlaces, udp, PORT):
	if(destination in enlaces):
		traceMessage = {
			'type': 'trace',
			'source': source,
			'destination': destination,
			'hops': [source]
		}
		print('sending traceMessage', traceMessage)
		fowardMessage(traceMessage, destination, enlaces, udp, PORT, source)
	else:
		print('Não é possível alcançar o roteador', destination)

def main(addr, period, startup):
	udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	PORT = 55151
	udp.bind((addr, PORT))
	enlaces = {}
	lastUpdates = {}

	sendUpdateThread = threading.Thread(target=sendUpdate, args=(addr, period, enlaces, PORT, udp))
	receiveMessageThread = threading.Thread(target=receivedMessage, args=(enlaces, lastUpdates, addr, udp, PORT))
	removeUnusedEnlacesThread = threading.Thread(target=removeUnusedEnlaces, args=(enlaces, lastUpdates, period))

	receiveMessageThread.start()
	sendUpdateThread.start()
	# Fica mais fácil de testar removendo isso aqui, não esquecer de descomentar
	# removeUnusedEnlacesThread.start()

	while(True):
		command = input().lower().split(' ')

		if(command[0] == 'add'):
			if(len(command) >= 3):
				addEnlace(command[1], command[2], enlaces, addr, lastUpdates)
			else:
				print('Invalid params, add should have an ip and weight.')
		elif(command[0] == 'del'):
			if(len(command) >= 2):
				delEnlace(command[1], enlaces, addr)
			else:
				print('Invalid params, del should have an ip')
		elif(command[0] == 'trace'):
			if(len(command) >= 2):
				sendTrace(command[1], addr, enlaces, udp, PORT)
		elif(command[0] == 'quit'):
			exit(1)
		else:
			print('Invalid command, please try again.')

if __name__ == "__main__":
	main(sys.argv[1], int(sys.argv[2]), len(sys.argv) == 4 and sys.argv[3])
