# SMS Desktop Application

Μια **Desktop** εφαρμογή σε **Python / Tkinter** - για όλα τα λειτουργικά συστήματα που υποστηρίζουν **Python / Tkinter** - για την αποστολή **SMS** μέσω του **HTTP**

**Σύντομα διαθέσιμη σε όλους τους ενδιαφερόμενους με την  - σχετική πάντα - ολοκλήρωση του Debug**  

Η εφαρμογή δημιουργήθηκε με σκοπό τη μελέτη της δημιουργίας ενός GUI με την χρήση της Python και του TKinter. Αποδείχθηκε αρκετά πολύπλοκη καθώς αφήνει πολλές λεπτομέρειες της υλοποίησης στην φροντίδα του προγραμματιστή. Σε κάθε περίπτωση μου έδωσε μια ιδέα για την μεθοδολογία υλοποίησης ενός  GUI στην Python.

### Συνοπτική περιγραφή:  

Η εφαρμογή παρέχει την δυνατότητα αποστολής SMS μέσω ενός παρόχου υπηρεσιών SMS Gateway και με την χρήση ενός φιλικού GUI για τον τελικό χρήστη. Περιλαμβάνει τη δυνατότητα μαζικής εισαγωγής στοιχείων από αρχείο csv (με κωδικοποίηση UTF) και την αποθήκευσή τους σε μια βάση δεδομένων SQLite που υποστηρίζεται εύκολα από την Python. Παρέχονται πλήρεις CRUD δυνατότητες επί των εγγραφών μέσω ενός κατάλληλου user interface

**Η εφαρμογή αποτελείται από ένα κύριο αρχείο Python στο οποίο υπάρχει η υλοποίησή της.** 

Συνοδεύεται από δύο ακόμα αρχεία.

Το πρώτο **parameters.txt** περιέχει τις παρακάτω παραμέτρους: 

 - key='xxxxxxxxxxxx'  <-- **Το κλειδί πρόσβασης στον πάροχο**
 - origin='Mexri 10Ch'  <-- **Το πεδίο From που θα εμφανίζεται ως αποστολέας του SMS**
- url='https://easysms.gr/api/'  <-- **Το entry point για τον πάροχο easysms**
- send_url='sms/send'    <-- **To send endpoint για την αποστολή**
- history_url='history/single/list'  <-- **To history endpoint** 
- balance_url='me/balance' <-- **To balance endpoint που εμφανίζει το υπόλοιπο των SMS που έχουμε στον λογαριασμό μας**


To αρχείο αυτό πρέπει να φορτωθεί πριν τη χρήση της εφαρμογής (κουμπί *Φόρτωση Παραμέτρων* στην καρτέλα *Παράμετροι Κέντρου SMS)* ώστε να μπορεί να γίνεται η επικοινωνία με το SMS Gateway. 
H εφαρμογή επιτρέπει απευθείας την τροποποίηση των βασικών παραμέτρων key , origin , url ενώ θα πρέπει με edit στο αρχείο parameters.txt να τροποποιηθούν οι παράμετροι  send_url , history_url και balance_url

Ως SMS Gateway, επέλεξα την εταιρία easysms.gr όπως είχα κάνει και στην web-based εφαρμογή. Η εφαρμογή μετατρέπεται εύκολα για όλους τους παρόχους SMS Gateway υπηρεσιων που παρέχουν REST API. 

To **δεύτερο (προαιρετικό)** είναι το αρχείο CSV που περιέχει τις εγγραφές που επιθυμούμε να εισάγουμε μαζικά στη βάση δεδομένων SQLite της εφαρμογής.
Μπορεί να έχει οποιοδήποτε όνομα αφού επιλέγεται μέσω ενός File Dialog παραθύρου και έχει την μορφή: 

**afm;name;surname;fathersname;mobile;other**
Ενδεικτικά μια εγγραφή είναι της μορφής: 

10000000; ΟΝΟΜΑ ; ΕΠΩΝΥΜΟ; ΠΑΤΡΩΝΥΜΟ;6900000000;ΠΛΗΡΟΦΟΡΙΕΣ

***Στο repository παρέχεται ενδεικτικά το αρχείο TEL.csv με μια ενδεικτική εγγραφή.*** 


**ΠΡΟΣΟΧΗ:** 

 - Η κωδικοποίηση των εγγραφών στο αρχείο CSV πρέπει να είναι UTF (προτείνεται το Notepad ++)
 - Θα πρέπει να γίνει η εγκατάσταση των βιβλιοθηκών requests και pillow ως εξής: 
	 - pip install requests
	 - pip install pillow



Μερικές εικόνες:

![Οθόνη Παραμέτρων](http://users.sch.gr/chertour/sms_desktop/Screen1.png)
![Οθόνη Αποστολής](http://users.sch.gr/chertour/sms_desktop/Screen2.png)
![Οθόνη Μαζικής Αποστολής](http://users.sch.gr/chertour/sms_desktop/Screen3.png)
![Οθόνη Αρχείου Απεσταλμένων](http://users.sch.gr/chertour/sms_desktop/Screen4.png)
![Οθόνη Διαχείρισης](http://users.sch.gr/chertour/sms_desktop/Screen5.png)



Τελευταία Ενημέρωση : 6/8/2020 

## License
[GPLv3](https://choosealicense.com/licenses/gpl-3.0/)
