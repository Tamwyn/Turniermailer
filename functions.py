import mysql.connector
import datetime

#Stelle eine Verbindung zur Turniermanagement Datenbank her
cnxTurnier = mysql.connector.connect(user='root', password='', host='localhost', database='turniermanagment')

#Stelle eine Verbindung zur Datenbank mit den Daten der Fechter her
cnxFechter = mysql.connector.connect(user='root', password='', host='localhost', database='fechten')

def GetTournaments():
	#Abfrage nach den Turnieren in den naechsten 6 Wochen
	cursor = cnxTurnier.cursor()
	query =  ("SELECT ID , Name , Datum, Ort, Ausschreibung From turnier WHERE Datum BETWEEN %s AND %s AND casted = 0")

	today = datetime.date.today()
	nextDate = datetime.date.today() + datetime.timedelta(weeks=6)

	cursor.execute(query, (today, nextDate)) #Fuehre die SQL Abfrage aus und ersetze die %s Platzhalter durch die angegebenen Variablen

	tournaments = cursor.fetchall()
	cursor.close()

	return tournaments
		

def GetAndProcessData(tournaments):
		
	for rows in tournaments:
		
		altersklassen = GetAge(rows[0])  #Frage erweiterte Daten zu dem Turnier ab. Dafuer wird jeweils die ID uebergeben
										#AltersklassenIDs
		weapons = CheckWeapon(rows[0]) #WaffenIDs

		fechter = FindFencers(altersklassen , weapons )#Suche nach Fechtern fuer die dieses Turnier geeignet ist
														#FechterIDs (Liste vom Typ set ->Jeder Wert nur einmal)
		informQuery = list() #Haenge FechterIDs und TurnierIDs hintereinander jede Fechter ID kann pro TurnierID nur einmal vorhanden sein

	return informQuery

def GetAge(TurID):
	cursor = cnxTurnier.cursor()

	query = ("SELECT JahrgID FROM altersklassen WHERE TurnierID =")
	query += str(TurID) #Da ein insert via %s fehlschlug der umweg ueber append
	cursor.execute(query)
    
	result = cursor.fetchall()
	cursor.close()
	
	return result


def CheckWeapon(TurID):
	cursor = cnxTurnier.cursor()
	
	query = ("SELECT WaffeID FROM waffetur WHERE TurnierID =")
	query += str(TurID) #Da ein insert via %s fehlschlug der umweg ueber append
	cursor.execute(query)
	
	result = cursor.fetchall()
	cursor.close()
	
	return result

def FindFencers(altersklassen, weapons):
	
	cursorFechter = cnxFechter.cursor()
	cursorJahrg   = cnxTurnier.cursor()

	matchingFencers = list()  #Die Fechter die informiert werden sollen. (Liste)

	for rowAK in altersklassen:
		queryZeitraum = ("SELECT Beginn , Ende FROM jahrgaenge WHERE ID =")
		queryZeitraum += str(rowAK[0]) #Appende die Jahrgangs ID an die Query
		 
		cursorJahrg.execute(queryZeitraum)
		zeitraum = cursorJahrg.fetchall() 

		for rowZ in zeitraum: #Speichere den Zeitraum in lesbareren Variablen
		 	beginn = rowZ[0]
		 	ende = rowZ[1]

		queryFencers = ("SELECT ID FROM fechter WHERE JAHRGANG BETWEEN %s AND %s")

		cursorFechter.execute(queryFencers, (beginn , ende)) #Fuege Beginn und Ende beim Between ein

		fechter = cursorFechter.fetchall() #Fechter mit uebereinstimmendem Jahrgang
		
		for rowF in fechter: #Nimm den Fechter
		 	queryWaffe = ("SELECT WaffeID FROM fechterwaffe WHERE FechterID =")
		 	queryWaffe += str(rowF[0]) #Appende die FechterID

		 	cursorFechter.execute(queryWaffe)
		 	fechterwaffe = cursorFechter.fetchall()

		 	for rowW in weapons: #Pruefe ob die Waffe fuer diesen Fechter mit der des 
		 						 #Turniers uebereinstimmt
		 		if rowW[0] in (fechterwaffe[0]): #Index out of Range
		 			matchingFencers.add(rowF[0])

	set(matchingFencers)
	print(matchingFencers)
	return matchingFencers


	cursorFechter.close()
	cursorJahrg.close()

def Inform(informQuery):
	print("Informiert")

#Schließe die Verbindung zu den Datenbanken
cnxTurnier.close()
cnxFechter.close()