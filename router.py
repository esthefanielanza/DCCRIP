# coding=utf-8
import select, socket, sys, json, threading, time, struct

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

def routeMessage(source, destinaton, typeT, payload):
	outMessage = {
		"source": source,
		"destination": destination,
		"type": typeT,
		"payload":payload										
	}
	return json.dumps(outMessage)

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

def getShortestPath(enlaces, ip):
	smallerDistance = sys.maxsize
	if(ip in enlaces):
		for neighborhood in enlaces[ip]:
			if int(enlaces[ip][neighborhood]) < smallerDistance:
				smallerDistance = int(enlaces[ip][neighborhood])
	return smallerDistance

def updateDistances(enlaces, ipRouter, smallestDistanceToUpdatedNode, newSmallestDistanceToUpdatedNode):
	for ip in enlaces:
		for gateway in enlaces[ip]:
			if(gateway == ipRouter):
				enlaces[ip][gateway] += newSmallestDistanceToUpdatedNode - smallestDistanceToUpdatedNode

def receivedUpdate(message, enlaces):
	# Existe caminho para esse roteador? Se sim, posso adicionar os caminhos dele
	#print('\n\n\n ======= RECEIVING ========')
	## print(message)
	#print('\n')
	if(message['source'] in enlaces):
		shortestDistanceToGateway = getShortestPath(enlaces, message['source'])
		# Para todos os ips
		for ip in list(enlaces):
			# Calculamos a menor distancia para este ip
			shortestDistanceToIp = getShortestPath(enlaces, ip)
			# Atualizamos ou deletamos se ele não estiver na mensagem
			if(ip in message['distances']):
				enlaces[ip][message['source']] = int(message['distances'][ip]) + shortestDistanceToGateway

			if(message['source'] in list(enlaces[ip]) and not ip in message['distances']):
				delEnlace(ip, enlaces, message['source'])

			newShortestDistanceToIp = getShortestPath(enlaces, ip)
			# A menor distancia mudou? Se sim devemos atualizar todos os nós
			if(not newShortestDistanceToIp == shortestDistanceToIp):
				#print('Should update distances')
				updateDistances(enlaces, ip, shortestDistanceToIp, newShortestDistanceToIp)

		# Verificamos se conseguimos alcançar algum novo ip
		for ip in message['distances']:
			if(not ip in enlaces):
				enlaces[ip] = {}
				enlaces[ip][message['source']] = int(message['distances'][ip]) + shortestDistanceToGateway
		
		print(enlaces)
		print('\n')

def receivedMessage(udp, enlaces):
	while(True):
		data,address = udp.recvfrom(65536)
		message = json.loads(data.decode('latin1'))
		if(message['type'] == 'update'):
			receivedUpdate(message, enlaces)
		elif(message['type'] == 'data'):
			print('Data message')
		elif(message['type'] == 'trace'):
			print("Trace message")						
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

def main(addr, period, startup):
	udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	PORT = 55151
	udp.bind((addr, PORT))
	enlaces = {}
	
	sendUpdateThread = threading.Thread(target=sendUpdate, args=(addr, period, enlaces, PORT, udp))
	receiveMessageThread = threading.Thread(target=receivedMessage, args=(udp, enlaces))

	receiveMessageThread.start()
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
				delEnlace(command[1], enlaces, addr)
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
