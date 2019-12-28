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
		
		Timeslot.comment.append("Дни (d) нумеруются: с 1 (ПН) по 5 (ПТ), затем 6 (ПН) и до 10 (ПТ)")
		Timeslot.comment.append("Часы (h) нумеруются номерами пар: 1 (с 8:30 по 10:00) по 6 (с 17:00 по 18:30)")
				
				
		######## General Properties ########
		
		# >
		# class referencesTo( AsymmetricProperty, IrreflexiveProperty): pass  # direct part
		# class referencedBy( InverseFunctionalProperty, AsymmetricProperty, IrreflexiveProperty): pass  # direct part
		# >
		# class isPartOf( FunctionalProperty, AsymmetricProperty, IrreflexiveProperty): pass  # direct part
		# >
			# class hasSibling( FunctionalProperty, InverseFunctionalProperty, AsymmetricProperty, IrreflexiveProperty): pass  # (directed) base for any Next
			# >
			# class hasPartTransitive( TransitiveProperty,  # transitive !
			# 	FunctionalProperty, AsymmetricProperty, IrreflexiveProperty): pass  # base for FirstAct
		# >
		# class hasUniqueData( FunctionalProperty, DataProperty): pass  # datatype property base
		referencesToUnique = [FunctionalProperty, AsymmetricProperty, IrreflexiveProperty]
		referencedByUnique = [InverseFunctionalProperty, AsymmetricProperty, IrreflexiveProperty]
		hasUniqueData = [FunctionalProperty, DataProperty]


		# Object properties
		
		class isPartOfTimetable( 	TimetableElement >> Timetable , *referencesToUnique): pass
		class takesPlace( 			Lesson >> Room , 				*referencesToUnique): pass
		class isAtTimeslot( 		Lesson >> Timeslot , 			*referencesToUnique): pass  # 0..*  -->  1 ; no ~~InverseFunctionalProperty~~ here
		class realizes( 			Lesson >> SubjAssignment , 		*referencesToUnique): pass
		class hasLearningAssignment( Group >> SubjAssignment , 		*referencedByUnique): pass
		class hasTeachingAssignment( Professor >> SubjAssignment , 	*referencedByUnique): pass
		class hasSubject( 			SubjAssignment >> Subject , 	*referencesToUnique): pass


		# Derived Object properties
		
		class attends( (Group | Professor) >> Lesson , AsymmetricProperty, IrreflexiveProperty): pass
		
		
		# Data properties
		
		class weekDays( 	Timetable >> int , *hasUniqueData): pass
		class dayHours( 	Timetable >> int , *hasUniqueData): pass
		class maxGroupHours( Timetable >> int , *hasUniqueData): pass
		class maxProfHours ( Timetable >> int , *hasUniqueData): pass
		
		class capacity( Room >> int , *hasUniqueData): pass
		
		class day ( Timeslot >> int , *hasUniqueData): pass
		class hour( Timeslot >> int , *hasUniqueData): pass
		
		class size( Group >> int , *hasUniqueData): pass

		
		# class hasName( (Or([Group,Professor,Subject,Room,Lesson])) >> str , *hasUniqueData): pass
		class hasName( Lesson >> str , *hasUniqueData): pass
		
		# class hours( SubjAssignment >> int , *hasUniqueData): pass
		
		
		# persistent instances (global objects)
		t = Timetable("TABLE")		  # to access to global options:
		t.weekDays 		= settings["weekDays"]
		t.dayHours 		= settings["dayHours"]
		t.maxGroupHours = settings["maxGroupHours"]
		t.maxProfHours 	= settings["maxProfHours"]
		
		# Prepare empty timeslots for a week.
		# Format:  d<d>_h<h>  (see name4timeslot() function)
		for d in range(1, 1+t.weekDays):
			for h in range(1, 1+t.dayHours):
				name = name4timeslot(d, h)
				slot = Timeslot(name)
				slot.isPartOfTimetable = t
				slot.day  = d
				slot.hour = h
				
		# CLOSE WORLD around all the Timeslot individuals - experimental for the lab!
		# close_world(Timeslot)
			
		
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
takesPlace(?L2, ?r),
hasName(?L1, ?Lname),
stringConcat(?msg, "Lessons clash at Room. One is: ", ?Lname)
 -> hasError(ERRORS, ?msg)
 """)
		# `differentFrom` -> `DifferentFrom` in owlready2 !!!
# 2. Вместимость аудитории менее численности группы, занятие у которой там проходит
		Imp().set_as_rule("""
Room(?r), Lesson(?L), Group(?g), 
attends(?g, ?L),
takesPlace(?L, ?r),
capacity(?r, ?cap), size(?g, ?n), 
lessThan(?cap, ?n),
hasName(?L, ?Lname),
stringConcat(?msg, "Room overflow with students at lesson: ", ?Lname)
 -> hasError(ERRORS, ?msg)
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
hasTeachingAssignment(?p, ?sa), 
realizes(?L, ?sa)
 -> attends(?p, ?L)
""")
# 4.1 Перегрузка в день для Group
		Imp().set_as_rule(make_overload_rule('Group', t.maxGroupHours))
# 4.2 Перегрузка в день для Professor
		Imp().set_as_rule(make_overload_rule('Professor', t.maxProfHours))
		

def make_overload_rule(subj='Group', max_lessons=4):

    n_excceed = max_lessons + 1
    
    from functools import reduce
    from operator import add
    import itertools

    linear_template = '''Lesson(?L{i}), Timeslot(?s{i}), day(?s{i}, ?d), 
	isAtTimeslot(?L{i}, ?s{i}), attends(?g, ?L{i}), 
	'''
    LessonTimeslot_declare = reduce(add, [linear_template.format(i=i) for i in range(n_excceed)])
    
    # comb_template = '''DifferentFrom(?L{i}, ?L{j}), 
    comb_template = '''DifferentFrom(?s{i}, ?s{j}), 
	'''
    differenceAssertions_declare = reduce(add, [comb_template.format(i=i, j=j) for i,j in itertools.combinations(range(n_excceed), 2)])
    
    return """
	{subj}(?g), 
	{LessonTimeslot_declare}{differenceAssertions_declare}
	stringConcat(?msg, "{subj} is overloaded at day ", ?d)
	 -> hasError(ERRORS, ?msg)
	""".format(subj=subj, LessonTimeslot_declare=LessonTimeslot_declare, differenceAssertions_declare=differenceAssertions_declare)

def name4timeslot(d=1, h=1):
	# return "slot%d_%d" % (d, h)
	return "d%d_h%d" % (d, h)
		

				
def assign(onto, prof_name, subject_name, group_name):
	''' Bings the three to new SubjAssignment node and returns the node '''
	prof 	= onto.Professor(prof_name)
	subject = onto.Subject(subject_name)
	group 	= onto.Group(group_name)
	sa_name = '%s-%s-%s' % (prof_name, subject_name, group_name)
	sa_name = ''.join(sa_name.split())  # remove all whitespaces
	with onto:
		sa = onto.SubjAssignment(sa_name)
		sa.hasSubject = subject  # sa.hasSubject.append(subject)  if sa.hasSubject  else [subject]
		prof.hasTeachingAssignment.append(sa)
		group.hasLearningAssignment.append(sa)
	return sa
	
def setLesson(onto, sa, room_name, timeslot_name):
	''' Bings the three to new Lesson node and returns the node 
	Note `sa` is object while'''
	room 	= onto.Room(room_name)
	timeslot= onto.Timeslot(timeslot_name)
	lesson_name = '%s_in%s_@%s' % (sa.name, room_name, timeslot_name)
	with onto:
		lesson 	= onto.Lesson(lesson_name)
		lesson.hasName = lesson_name
		lesson.realizes = sa
		lesson.isAtTimeslot = timeslot
		lesson.takesPlace = room
		lesson.isPartOfTimetable = onto.TABLE
	return lesson
				

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


def fill_ok_timetable(onto):
	
	with onto:
		# we may omit declaration property-less individuals; they will be created on first access.
		# onto.Professor('Орлова')
		# onto.Professor('Игнатьев')
		# onto.Professor('Гилка')
		# onto.Professor('Пром')
		# onto.Professor('Аникин')
		# onto.Professor('Мига')
		# onto.Professor('Литовкин')
		
		# onto.Subject('НИР')
		# onto.Subject('АнализДанных')
		# onto.Subject('Английский')
		# onto.Subject('СУБД')
		# onto.Subject('БазыДанных')
		# onto.Subject('AБAБЫ')
		# onto.Subject('Программирование')
		
		# declare properties for concrete individuals to use further
		onto.Group('ПОАС1.1', size = 12)
		onto.Group('ПОАС1.2', size = 11)
		onto.Group('ПрИн-266', size = 18)
		
		onto.Room('902').capacity = 50
		onto.Room('903').capacity = 20
		onto.Room('1003').capacity = 27
		onto.Room('300а').capacity = 12
		
	# assign(onto, prof_name, subject_name, group_name):
	nir = assign(onto, 'Орлова', 'НИР', 'ПОАС1.1')
	ad0 = assign(onto, 'Игнатьев',  'АнализДанных', 'ПОАС1.1')
	adh = assign(onto, 'Гилка', 	'АнализДанных', 'ПОАС1.1')
	eng1 = assign(onto, 'Пром', 'Английский', 'ПОАС1.1')
	eng2 = assign(onto, 'Пром', 'Английский', 'ПОАС1.2')
	bd = assign(onto, 'Аникин', 'СУБД', 'ПОАС1.1')	
	abap = assign(onto, 'Мига', 'AБAБЫ', 'ПОАС1.1')	
	prog = assign(onto, 'Литовкин', 'Программирование', 'ПрИн-266')	
	
	# setLesson(onto, sa, room_name, timeslot_name):
	# ассистирование у Литовкина
	setLesson(onto, prog, '902', name4timeslot(d=2, h=4))
	setLesson(onto, prog, '902', name4timeslot(d=2, h=3))
	
	setLesson(onto, nir, '903', name4timeslot(d=2, h=5))
	setLesson(onto, nir, '903', name4timeslot(d=2, h=6))
	
	setLesson(onto, adh, '1003', name4timeslot(d=3, h=2))
	# setLesson(onto, ad0, '903', name4timeslot(d=3, h=3))
	setLesson(onto, adh, '902', name4timeslot(d=3, h=3))
	setLesson(onto, adh, '902', name4timeslot(d=3, h=4))
	
	setLesson(onto, eng1, '300а', name4timeslot(d=5, h=1))
	setLesson(onto, eng1, '300а', name4timeslot(d=5, h=2))
	setLesson(onto, eng2, '300а', name4timeslot(d=5, h=3))
	setLesson(onto, eng2, '300а', name4timeslot(d=5, h=4))
	
	setLesson(onto, bd, '903', name4timeslot(d=6, h=2))
	setLesson(onto, bd, '903', name4timeslot(d=6, h=3))
	setLesson(onto, bd, '903', name4timeslot(d=6, h=4))

	setLesson(onto, abap, '902', name4timeslot(d=7, h=3))
	setLesson(onto, abap, '902', name4timeslot(d=7, h=4))

	# ассистирование у Литовкина
	setLesson(onto, prog, '902', name4timeslot(d=9, h=1))
	setLesson(onto, prog, '902', name4timeslot(d=9, h=2))
	
	setLesson(onto, adh, '903', name4timeslot(d=9, h=3))
	setLesson(onto, adh, '903', name4timeslot(d=9, h=4))
	

def main():

	onto_iri = 'http://poas1.time/table'
	ttbl = get_ontology(onto_iri)
	
	# Считать "часы" "парами", для упрощения расчётов.
	# т.е. "6 пар в день"  ==>  "12 часов в день" --> запишем "hours" = 6
	settings = {
		"weekDays"  : 12,
		"dayHours" : 6,
		"maxGroupHours" : 3,
		"maxProfHours" : 1,
	}
	
	make_timetable_schema(ttbl, settings)
	print("schema ready")
	
	fill_ok_timetable(ttbl)
	print("data ready")
	
	
	# close_world(ttbl)
	# print("world closed!")
	
	ttbl.save(file='timetable_schema.rdf', format='rdfxml')
	print("Saved RDF file!")
	
	return ######################################################## ! !
				
	
	upload_rdf_to_SPARQL_endpoint('http://localhost:3030/ttbl/data', 'timetable_schema.rdf')
				
				
if __name__ == '__main__':
	main()