#Formatiere die verschachtelten Tuples zu einer einfachen Liste
def format(cursor): 
	result = list()
	for dump in cursor:
		result.append(dump[0])

	return result