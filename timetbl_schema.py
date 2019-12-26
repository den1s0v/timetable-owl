""" Creating timetable_schema ontology from scratch with code using owlready2.
 Manual: https://owlready2.readthedocs.io/en/latest 
 
 --------------------------------
 $ pip install owlready2
 
 --------------------------------
 
 """

from owlready2 import *




def make_timetable_schema(onto, settings):
	with onto:
		
		# classes
		
		class Timetable(Thing): pass
		class TimetableElement(Thing): pass
		class Room(Thing): pass
		class Lesson(TimetableElement): pass
		class Timeslot(TimetableElement): pass
		class Group(Thing): pass
		class Subject(Thing): pass
		class SubjAssignment(Thing): pass
		class Professor(Thing): pass
				
		######## General Properties ########
		
		# >
		class referencesTo( FunctionalProperty, AsymmetricProperty, IrreflexiveProperty): pass  # direct part
		class referencedBy( InverseFunctionalProperty, AsymmetricProperty, IrreflexiveProperty): pass  # direct part
		# >
		class hasPart( FunctionalProperty, AsymmetricProperty, IrreflexiveProperty): pass  # direct part
		# >
			# class hasSibling( FunctionalProperty, InverseFunctionalProperty, AsymmetricProperty, IrreflexiveProperty): pass  # (directed) base for any Next
			# >
			# class hasPartTransitive( TransitiveProperty,  # transitive !
			# 	FunctionalProperty, AsymmetricProperty, IrreflexiveProperty): pass  # base for FirstAct
		# >
		class hasUniqueData( FunctionalProperty, DataProperty): pass  # datatype property base



		# Object properties
		
		class isPartOfTimetable( TimetableElement >> Timetable , hasPart): pass
		class takesPlace( Lesson >> Room , referencesTo): pass
		class isAtTimeslot( Lesson >> Timeslot , referencesTo): pass  # 0..*  -->  1 ; no ~~InverseFunctionalProperty~~ here
		class realizes( Lesson >> SubjAssignment , referencesTo): pass
		class hasLearningAssignment( Group >> SubjAssignment , referencedBy): pass
		class hasTeachingAssignment( Professor >> SubjAssignment , referencedBy): pass
		class hasSubject( SubjAssignment >> Subject , referencesTo): pass


		# Derived Object properties
		
		class attends( (Group | Professor) >> Lesson , AsymmetricProperty, IrreflexiveProperty): pass
		
		
		# Data properties
		
		class weekDays( Timetable >> int , hasUniqueData): pass
		class dayHours( Timetable >> int , hasUniqueData): pass
		class maxGroupHours( Timetable >> int , hasUniqueData): pass
		class maxProfHours ( Timetable >> int , hasUniqueData): pass
		
		class capacity( Room >> int , hasUniqueData): pass
		
		class day ( Timeslot >> int , hasUniqueData): pass
		class hour( Timeslot >> int , hasUniqueData): pass
		
		class size( Group >> int , hasUniqueData): pass

		
		class name( (Group | Professor | Subject | Room) >> str , hasUniqueData): pass
		class hours( SubjAssignment >> int , hasUniqueData): pass
		
		
		# persistent instances (global objects)
		t = Timetable("TABLE")		  # to access to global options:
		t.weekDays 		= settings["weekDays"]
		t.dayHours 		= settings["dayHours"]
		t.maxGroupHours = settings["maxGroupHours"]
		t.maxProfHours 	= settings["maxProfHours"]
		
		# Prepare empty timeslots for a week
		for d in range(1, 1+t.weekDays):
			for h in range(1, 1+t.dayHours):
				name = "slot%d_%d" % (d, h)
				slot = Timeslot(name)
				slot.isPartOfTimetable = t
				slot.day  = d
				slot.hour = h
				
			
		
		# SWRL Rules
		
		class TimetableError( Thing ): pass
		class hasError( TimetableError >> str, DataProperty ): pass
		
		# persistent instances (global objects)
		TimetableError("ERRORS")  # to attach log messages
		
	
# 1. В одной аудитории (Room) проходит более одного урока одновременно
		Imp().set_as_rule("""
Room(?r), Timeslot(?s), Lesson(?L1), Lesson(?L2),
DifferentFrom(?L1, ?L2),
isAtTimeslot(?L1, ?s),
isAtTimeslot(?L2, ?s),
takesPlace(?L1, ?r),
takesPlace(?L2, ?r)
 -> hasError(ERRORS, "Lessons clash at Room")
 """)
		# `differentFrom` -> `DifferentFrom` in owlready2 !!!
# 2. Вместимость аудитории менее численности группы, занятие у которой там проходит
		Imp().set_as_rule("""
Room(?r), Lesson(?L), SubjAssignment(?sa), Group(?g), 
attends(?g, ?L),
takesPlace(?L, ?r),
capacity(?r, ?cap), size(?g, ?n), 
lessThan(?cap, ?n)
 -> hasError(ERRORS, "Room overflow with students")
""")
# 3.1 Вывод attends из назначения для Group
		Imp().set_as_rule("""
Lesson(?L), SubjAssignment(?sa), Group(?g), 
hasLearningAssignment(?g, ?sa), 
realizes(?L, ?sa)
 -> attends(?g, ?L)
""")
# 3.2 Вывод attends из назначения для Professor
		Imp().set_as_rule("""
Lesson(?L), SubjAssignment(?sa), Professor(?p), 
hasLearningAssignment(?p, ?sa), 
realizes(?L, ?sa)
 -> attends(?p, ?L)
""")
# 4.1 Перегрузка в день для Group
		
		
		
		


def set_instances(onto, prop_list):
	
	""" prop_list: list of dicts:
	{
		"class": any_WL_Class,
		"names": list of str,
	}  """
	
	with onto:
		for prop in prop_list:
			cl = prop["class"]
			for name in prop["names"]:
				cl.__call__(name)  # make an individual
				

def upload_rdf_to_SPARQL_endpoint(graphStore_url, rdf_file_path):
	import requests
	with open(rdf_file_path, 'rb') as f:
		r = requests.post(
		    graphStore_url,  # ex. 'http://localhost:3030/my_dataset/data', 
		    files={'file': ('onto.rdf', f, 'rdf/xml')}
		)

	if r.status_code != 200:
		print('\nError uploading file! HTTP response code: %d\nReason: %s\n' % (r.status_code, r.reason))
		return False
	else:
		print('Uploading file successful.')
		return True
    

###############################################################

def main():

	onto_iri = 'http://vstu.ru/poas/s09/timetable'
	ttbl = get_ontology(onto_iri)
	
	# Считать "часы" "парами", для упрощения расчётов.
	# т.е. "12 часов в день" / 2  ==>  "6 пар в день"
	settings = {
		"weekDays"  : 6,
		"dayHours" : int(12/2),
		"maxGroupHours" : int(8/2),
		"maxProfHours" : int(6/2),
	}
	
	make_timetable_schema(ttbl, settings)
	
	print("schema ready")
	
	# set_instances(ttbl, [
	# 	{
	# 	"class": ttbl.Group,
	# 	"names": ["POAS1.1","POAS1.2"]
	# 	}])
	
	# print("instances ready")
	
	# ttbl.save(file='timetable_schema.rdf', format='rdfxml')
	# print("Saved RDF file!")
	
	return ######################################################## ! !
				
	
	upload_rdf_to_SPARQL_endpoint('http://localhost:3030/ttbl/data', 'timetable_schema.rdf')
				
				
if __name__ == '__main__':
	main()