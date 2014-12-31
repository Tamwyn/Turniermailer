import mysql.connector
import datetime
import functions as fct

tournaments = fct.GetTournaments() #Rufe eine Liste der Turniere ab
informQuery = fct.GetAndProcessData(tournaments) #Rufe eine Liste mit FechterIDs und zugewiesenen TurnierIDs ab

fct.Inform(informQuery)#Versende Emails mit den Ausschreibungen