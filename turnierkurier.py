import mysql.connector
import datetime
#Stelle eine Verbindung zur Turniermanagement Datenbank her
cnxTurnier = mysql.connector.connect(user='root', password='', host='localhost', database='turniermanagment')

#Stelle eine Verbindung zur Datenbank mit den Daten der Fechter her
cnxFechter = mysql.connector.connect(user='root', password='', host='localhost', database='fechten')

def GetTournaments():
	#Abfrage nach den Turnieren in den naechsten 6 Wochen
	cursor = cnxTurnier.cursor()
	query =  ("SELECT ID From turnier WHERE Datum BETWEEN %s AND %s AND casted = 0")

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
														#FechterIDs (Liste vom Typ set ->Jeder Wert nur einmal (set)
		informQuery = list()

		for rowF in fechter:
			informQuery.append((rowF[0], rows[0])) #Haenge FechterIDs und TurnierIDs hintereinander jede Fechter ID kann pro TurnierID nur einmal vorhanden sein

	return informQuery

	return "false"

def GetAge(TurID):
	cursor = cnxTurnier.cursor()

	query = ("SELECT JahrgID FROM altersklassen WHERE TurnierID =")
	query += str(TurID) #Da ein insert via %s fehlschlug der Umweg ueber append
	cursor.execute(query)
    
	result = cursor.fetchall()
	cursor.close()
	
	return result


def CheckWeapon(TurID):
	cursor = cnxTurnier.cursor()
	query = ("SELECT WaffeID FROM waffetur WHERE TurnierID =")
	query += str(TurID) #Da ein insert via %s fehlschlug der Umweg ueber append
	cursor.execute(query)
	result = list()
	
	for dump in cursor.fetchall(): #Aufgrund des Rückgabeformats von fetchall mit verschachtelten Tuples diese Loesung
		result.append(dump[0])
	
	cursor.close()
	
	return result

def FindFencers(altersklassen, weapons):
	
	cursorFechter = cnxFechter.cursor()
	cursorJahrg   = cnxTurnier.cursor()

	matchingFencers = list()  #Die Fechter deren Waffe und Altersklasse mit der des Turniers uebereinstimmen (Liste)

	for rowAK in altersklassen:
		queryZeitraum = ("SELECT Beginn , Ende FROM jahrgaenge WHERE ID =")
		queryZeitraum += str(rowAK[0]) #Appende die Jahrgangs ID an die Query
		 
		cursorJahrg.execute(queryZeitraum)
		zeitraum = cursorJahrg.fetchall() 

		for rowZ in zeitraum: #Speichere den Zeitraum in lesbareren Variablen
		 	beginn = rowZ[0]
		 	ende = rowZ[1]

		
		queryFencers = ("SELECT DISTINCT ID  From fechter as f JOIN fechterwaffe AS fw ON f.ID = fw.FechterID WHERE Jahrgang BETWEEN %s AND %s AND WaffeID =") #Alle Fechter deren Geburtsjahr innerhalb der Range der erfragten Altersklasse liegt und ihre Waffe übereinstimmt
		
		if (len(weapons) == 1):
			queryFencers += str(weapons[0]) #Appende die ID der Waffe
			
		if (len(weapons) == 2): #Wenn ein Turnier fue Beide Waffen verfuegbar ist Frage auch beide ab. Druch DISTINCT erscheint jeder Fechter nur einmal
			queryFencers += str(weapons[0]) + " OR WaffeID =" + str(weapons[1])
			
		else:
			#Should never happen
			print("Keine Waffe angegeben im Turnier")
			#break
		cursorFechter.execute(queryFencers, (beginn , ende)) #Fuege Beginn und Ende beim Between ein
		matchingFencers.append(cursorFechter.fetchall())
		

	#set(matchingFencers) #Sorge dafür, dass für dieses Turnier jeder Fechter nur einmal vorhanden ist
	return matchingFencers


	cursorFechter.close()
	cursorJahrg.close()

def Inform(informQuery):
	print(informQuery)

tournaments = GetTournaments() #Rufe eine Liste der Turniere ab
informQuery = GetAndProcessData(tournaments) #Rufe eine Liste mit FechterIDs und zugewiesenen TurnierIDs ab

Inform(informQuery)#Versende Emails mit den Ausschreibungen

#Schliesse die Verbindung zu den Datenbanken
cnxTurnier.close()
cnxFechter.close()