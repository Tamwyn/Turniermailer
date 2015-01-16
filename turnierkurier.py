#coding=utf-8
#Setze das encoding auf utf-8 um spaetere Probleme umgehen zu koennen mit Sonderzeichen

#Importiere die Bibliotheken zur Darstellung von Daten und fuer MySQL
import mysql.connector
import datetime

import formatize #Formatiere die Ausgaben der SQL Query in eine nuetzliches Dateiformat (siehe formatize.py)

##Die Email Module, welche zum Versand noetig sind (in Kombination mit einem SMTP Server) 
import smtplib
from email.mime.text import MIMEText

#####LOGLEVEL#############################################################
##Veraendere den Output des Loglevels um unterschiedlich praezise	##
##Daten zu bekommen:							##
##0 : keine; 								##
##1 : Die Werte der Variablen; 						##
##2 : Die SQL Queries;							##
loglvl = 0 								##
##########################################################################
try:
	#Versuche eine Verbindung zur Datenbank herzustellen
	cnxTurnier = mysql.connector.connect(user='root', password='password', host='localhost', database='turniermanagment')

	#Stelle eine Verbindung zur Datenbank mit den Daten der Fechter her
	cnxFechter = mysql.connector.connect(user='root', password='password', host='localhost', database='fechten')

except: #Der Datenbankserver ist anscheinend nicht erreichbar. Daher wird die Ausfuehrung abgebrochen
	exit("Die Datenbank konnte nicht erreicht werden")

###################################BEGIN FUNCTIONS##############################################

def GetTournaments():
	if (loglvl ==1): print("GetTournaments")#Debugging:Die Funktion wurde aufgerufen
	#Abfrage nach den Turnieren in den naechsten 6 Wochen, die noch nicht verarbeitet wurden.
	cursor = cnxTurnier.cursor() #Erstelle ein MySQL Cursor Objekt, welches in der Lage ist SQL Queries auszufuehren
	query =  ("SELECT ID From turnier WHERE Datum BETWEEN %s AND %s AND casted = 0") # %s sind Platzhalter.

	today = datetime.date.today() 
	nextDate = datetime.date.today() + datetime.timedelta(weeks=6) #Heute + 6 Wochen

	if (loglvl == 2): print ("Query: " + query + " Heute: " + str(today) + " Ende: " + str(nextDate))#Debugge ggf. die SQL Query

	cursor.execute(query, (today, nextDate)) #Fuehre die SQL Abfrage aus und ersetze die %s Platzhalter durch die angegebenen Variablen in den Klammern

	tournaments = formatize.format(cursor.fetchall()) #Uebergib das im Cursor gespeicherte Ergebnis aufgrund des eigenartigen Datenformats "(1,)" an die Funktion zur Formatierung und Speichere die Werte in der Variable (Typ: Liste)
	cursor.close() #Schließe den Cursor um eine Timeout der Datenbank zu verhindern

	if (loglvl ==1): print("TurnierIDs: " + str(tournaments)) #Debugging

	return tournaments #Gib die Liste der Turniere zurueck Format: "(TurnierID, TurnierID,...)"
		

def GetAndProcessData(TurID):
	if (loglvl ==1): print("GetAndProcessData")

	altersklassen = GetAge(TurID)  #Frage erweiterte Daten zu dem Turnier ab. Dafuer wird jeweils die ID uebergeben Ergebnis: AltersklassenIDs
	if (loglvl ==1): print("AKS: " + str(altersklassen)) 
		
	weapons = CheckWeapon(TurID) #WaffenIDs
	if (loglvl ==1): print("Waffe: " + str(weapons))

	fechter = FindFencers(altersklassen , weapons , TurID)#Suche nach Fechtern fuer die dieses Turnier geeignet ist
	if (loglvl ==1): print("Fechter(GetAndProcessData): " + str(fechter)) #Debugging

	return fechter #Diese Fechter sollen informiert werden


def GetAge(TurID): #Frage die Altersklassen fuer dieses Turnier ab
	if (loglvl == 1): print("GetAge")
	
	cursor = cnxTurnier.cursor()
	query = ("SELECT JahrgID FROM altersklassen WHERE TurnierID =")
	query += str(TurID) #Da ein insert via %s fehlschlug der Umweg ueber append
	if (loglvl == 2): print ("Query: " + query)
	
	cursor.execute(query)
    
	alterskl = formatize.format(cursor.fetchall()) #Auch hier wieder die Formatierung
	if (loglvl == 1): print ("Altersklassen:" + alterskl) #Debugging
	cursor.close()
	
	return alterskl #Gib die Altersklassen zurueck Format: Liste "(altersklID, altersklID,...)" 


def CheckWeapon(TurID): #Frage die Waffen fuer ein Turnier ab
	if (loglvl ==1): print("CheckWeapon")
	cursor = cnxTurnier.cursor()
	query = ("SELECT WaffeID FROM waffetur WHERE TurnierID =")
	query += str(TurID) #Da ein insert via %s fehlschlug der Umweg ueber append
	if (loglvl == 2): print ("Query: " + query)
	cursor.execute(query)
	
	weapon = formatize.format(cursor.fetchall()) #Fromatiere und gib eine Liste im Format "(WaffeID,WaffeID,...)" zurueck
	
	cursor.close()
	
	return weapon

def FindFencers(altersklassen, weapons, TurID): #Finde Fechter fuer auf die diese Bedingungen zutreffen 
	if (loglvl ==1): print("FindFencers")
	
	cursorFechter = cnxFechter.cursor()
	cursorJahrg   = cnxTurnier.cursor()

	matchingFencers = list()  #Die Fechter deren Waffe und Altersklasse mit der des Turniers uebereinstimmen (Liste)

	for rowAK in altersklassen: #Iteriere ueber die Liste der Alterklassen
		
		if (loglvl ==1): #Einige Debugging Infos
			print("")
			print("Turnier ID:  " + str(TurID))
			print("Altersklasse ID: " + str(rowAK))

		queryZeitraum = ("SELECT Beginn , Ende FROM jahrgaenge WHERE ID =")
		queryZeitraum += str(rowAK) #Appende die Jahrgangs ID an die Query
		if (loglvl == 2): print ("Zeitraum: " + queryZeitraum)
		cursorJahrg.execute(queryZeitraum)
		zeitraum = cursorJahrg.fetchall() #Da hier zwei Werte zurueck gegeben werden ist ein Formatieren nicht noetig

		for rowZ in zeitraum: #Speichere den Zeitraum in lesbareren Variablen
		 	beginn = rowZ[0]
		 	ende = rowZ[1]

		if (loglvl ==1): print("Beginn: " + str(beginn) + " Ende: " + str(ende))
		
		queryFencers = ("SELECT DISTINCT ID  From fechter as f JOIN fechterwaffe AS fw ON f.ID = fw.FechterID WHERE Jahrgang BETWEEN %s AND %s AND WaffeID =") #Alle Fechter deren Geburtsjahr innerhalb der erfragten Altersklasse liegt und ihre Waffe übereinstimmt
		
		if (len(weapons) == 1): #Ist das Turnier fuer eine oder zwei Waffen?
			queryFencers += str(weapons[0]) #Appende die ID der Waffe
			if (loglvl ==2): print("Eine WaffenID: " + str(queryFencers)) 
			
		if (len(weapons) == 2): #Wenn ein Turnier fuer deide Waffen verfuegbar ist, frage auch beide ab. Durch DISTINCT erscheint jeder Fechter nur einmal
			queryFencers += str(weapons[0]) + " OR WaffeID =" + str(weapons[1])
			if (loglvl ==2): print("Zwei WaffenIDs: " + str(queryFencers))
			
		else:
			#Should never happen, sonst informiere welches Turnier keine Waffen hat und beende
			exit("[ERR]Keine Waffe angegeben in diesem Turnier "+ str(TurID))
			
		
		cursorFechter.execute(queryFencers, (beginn , ende)) #Fuege Beginn und Ende beim Between (%s) ein
				
		matchingFencers.extend(formatize.format(cursorFechter.fetchall())) #Haenge die neuen Fechter an die matchingFencers Liste an.
		if (loglvl ==1): 
			print("matchingFencers: " + str(matchingFencers))	
			print("")
		
	cursorFechter.close()
	cursorJahrg.close()

	#Sorge dafuer, dass fuer dieses Turnier jeder Fechter nur einmal vorhanden ist
	#Eine Mehrfachselection kann durch Ueberschneidungen in den Altersklassen entstehen
	#set ist ein Datentyp, in dem jeder Wert nur einmal vorhanden sein kann
	uniqueFencers = list(set(matchingFencers))
	return uniqueFencers


def Inform(informQuery, TurID): #Schreibe die Emails
	if (loglvl ==1): print("Inform")
	if (loglvl ==1): print("Fechter IDs " + str(informQuery) + " fuer TurnierID: " + str(TurID))

	#Hole weitere Turnierangaben
	cursorTurnier = cnxTurnier.cursor()
	
	#Frage nun die Daten des Turniers ab, welche fuer eine Mail noetig sind
	queryTournament = ("SELECT Name , Ausschreibung , Pflichtturnier , Datum , Ort FROM turnier WHERE ID =")
	queryTournament += str(TurID)
	if (loglvl == 2): print(queryTournament)

	cursorTurnier.execute(queryTournament)
	dump = cursorTurnier.fetchall() #kein Formatize noetig aufrgund der Abfrage mehrerer Werte
	turnier = dump[0]

	TurName = turnier[0]
	TurLink = turnier[1]
	TurPflicht = turnier[2]
	TurDatum = turnier[3].strftime("%a, den %d. %b %Y")
	TurOrt = turnier[4]

	if (loglvl == 1):	
		print(TurName)
		print(TurLink)
		print(TurPflicht)
		print(TurDatum)
		print(TurOrt)
		print("Die Daten des Turniers: " + str(turnier))

	#####Erstelle die Email#####
	mail = "Hallo zusammen, \n"
	mail += "In kürze steht ein neues Turnier an:\n"
	mail += "Das " + str(TurName) + ".\n"
	mail += "Es findet am " + str(TurDatum) + " in " + str(TurOrt) + " statt.\n"
	mail += "Eine Ausschreibung findet sich unter folgendem Link: <a href='" + str(TurLink)  + "'>" +str(TurLink) + "</a>\n"
	if (TurPflicht == 1): mail += "Dieses Turnier ist ein wichtiges Turnier und es ist ärgerlich dieses zu verpassen\n"
	mail += "Bitte meldet euch rechtzeitig zurück, ob ihr starten könnt\n"
	mail += "Mit Fechtergruß\n"
	mail += "Das Turniermanagmentsystem des FC Lütjensee"

	mail = mail.decode('utf-8') #Konvertiere den Text zu utf-8

	if (loglvl == 1): print(mail)

	try: #Versuche eine Verbindung zum Mailserver herzustellen
		s = smtplib.SMTP('localhost')
	except:
		quit("Der Mailserver konnte nicht erreicht werden")

	msg = MIMEText(mail, 'plain', 'utf-8')
	msg["Subject"] = "Ein Turnier kommt: " + str(TurName)
	msg["From"] = "thore@datensumpf.de"

	cursorAdresse = cnxFechter.cursor()
	for fechter in informQuery:
		if (loglvl == 1): print("FechterID: " + str(fechter))
		
		queryMail = ("SELECT Email FROM fechter WHERE ID=") #Hole die Mailadresse des Fechters
		queryMail += str(fechter)
		if (loglvl == 2): print(queryMail)

		cursorAdresse.execute(queryMail)
		dump = formatize.format(cursorAdresse.fetchall())
		email = str(dump[0].decode("utf-8"))
		if (loglvl == 1): print("Emailadresse: " + email)

		#Verfollstaendige das Mail-Formular
		msg["To"] = email

		##Versende die Email##
		s.sendmail("thore@datensumpf.de", [email] , msg.as_string())
	
	s.quit() ##Schließe die Verbindung zum Mailserver

	cursorAdresse.close()	
	
def MarkTournament(TurID):
	if (loglvl ==1): print("MarkTournament")
	cursor = cnxTurnier.cursor()

	query = ("UPDATE turnier SET casted='1' WHERE ID=")
	query += str(TurID)
	if (loglvl == 2): print(query)

	cursor.execute(query) #Schreibe, dass das Turnier gecasted wurde und bestaetige mit commit
	cnxTurnier.commit()

##########################################END OF FUNCTIONS##############################################

########################################################################################################

##########################################BEGIN IMPLEMENTATION##########################################
tournaments = GetTournaments() #Rufe eine Liste der Turniere ab

for TurID in tournaments:
	informQuery = GetAndProcessData(TurID) #Rufe eine Liste mit FechterIDs und zugewiesenen TurnierIDs ab

	Inform(informQuery, TurID)#Versende Emails mit den Ausschreibungen an die Fechter fuer die dieses Turnier geeignet ist

	MarkTournament(TurID) #Speichere in der Datenbank, dass das Turnier gemeldet wurde




#Schliesse die Verbindung zu den Datenbanken
cnxTurnier.close()
cnxFechter.close()
