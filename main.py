from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import requests
import json
import csv
import time

# Launch a web browser
import webbrowser
# Manipulates date given as strings
from datetime import datetime
import sqlite3
#Splash Screen only related
from PIL import ImageTk,Image
# Global variables for allowing the exchange of information between the Tkinter Notebook Tabs
SMSKey = ''  # SMS Gateway paid key
SMSOriginator = ''  # Who will send the message
SMS_gateway_url = ''  # The Gateway URL
theRoot = ''  # Pointer to the root window
SEND_URL = '' # Pointer to SMS Send call
HISTORY_URL= '' # Pointer to SMS History call
BALANCE_URL ='' # Pointer to SMS Balance URL
'''
###################################################################################
The definition of the Class for creating a help tooltip
###################################################################################
'''


class CreateToolTip(object):
    # Create a tooltip for a given widget

    def __init__(self, widget, text='Μήνυμα Εφαρμογής'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)

    def enter(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # Creates a toplevel window
        self.tw = Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(self.tw, text=self.text, justify='left',
                      background='yellow', relief='solid', borderwidth=1,
                      font=("times", "12", "normal"))
        label.pack(ipadx=1)

    def close(self, event=None):
        if self.tw:
            self.tw.destroy()


'''
###################################################################################
The class containing the GUI elements to allow for the successful connection 
to the SMS Gateway
###################################################################################
'''


class SMSConfiguration:

    def __init__(self, SMSParametersContainer, CreateGuiReference, root):
        self.Label = []
        self.entryFields = []
        self.CreateGuiReference = CreateGuiReference
        '''
        We create a data structure to hold the values of:
         1. The fields we want to monitor and constantly save their status i.e.
            a. SMS Code provided by the SMS Gateway Services provider
            b. The origin you want to appear as the send from
            c. The URL accepting the SMS message 
        '''
        self.dictionaryList = ['Code', 'Origin', 'URL']
        self.watches = {}

        for field in self.dictionaryList:
            self.watches[field] = StringVar()

        self.SMSConfigurationFrame = ttk.Frame(SMSParametersContainer)
        self.SMSConfigurationFrame.pack(fill=BOTH, expand=1)
        self.label = ttk.Label(self.SMSConfigurationFrame, text="Παράμετροι κέντρου SMS", font=("Courier", 18),
                               background='yellow')
        self.label.grid(row=0, columnspan=3, pady=10)
        labels = ['Υπολοιπο SMS :', 'SMS Center Key:', 'Message Originator:', 'SMS Provider URL:']
        r = 0  # iterator value
        for content in labels:
            self.Label.append(ttk.Label(self.SMSConfigurationFrame, text=content, width=18))
            self.Label[r].grid(row=(r + 1), column=0, sticky='ew', pady=5)
            self.entryFields.append(ttk.Entry(self.SMSConfigurationFrame, width=29))
            self.entryFields[r].grid(row=(r + 1), column=1, sticky='ew', pady=5)
            self.entryFields[r].config(foreground='blue', background='yellow')
            r = r + 1

        '''
         Traverse dictionary and assign a textvariable=StringVar() to the correct GUI element
        '''

        # Configuring Message Originator to accept only 11 numbers

        def val(i):
            if int(i) > 10:
                return False
            return True

        self.vcmd = (root.register(val), '%i')
        self.entryFields[2].config(validate="key", validatecommand=self.vcmd)

        # Disable enrty field of sms quota
        self.entryFields[0].config(state='disable')

        SMS_quota = CreateToolTip(self.entryFields[0], "To πεδίο ενημερώνεται μετά την φόρτωση των παραμέτρων")

        for index, field in enumerate(self.watches):
            self.entryFields[index + 1].config(textvariable=self.watches[field])

        '''
        Identification about with tkinter entry box was modified:
        The callback caller passed internal Tkinter Variables called PY_VAR(2,3,4 ...)
        In our case SMSKEY = PY_VAR2 , SMSOriginator = PY_VA3 , SMS_URL=PY_VAR4
        With that information we update and changed variable for the users through the GUI Element
        Could be better engineered though ...
        '''

        def traceCallback(*args):
            field = args[0]

            global SMSKey, SMSOriginator, SMS_gateway_url, theRoot
            if field == 'PY_VAR0':
                SMSKey = self.watches['Code'].get()
                self.CreateGuiReference.SMSSendStandAloneRegion.svCode.set(SMSKey)
            elif field == 'PY_VAR1':
                SMSOriginator = self.watches['Origin'].get()
                self.CreateGuiReference.SMSSendStandAloneRegion.svOrigin.set(SMSOriginator)
            elif field == 'PY_VAR2':
                SMS_gateway_url = self.watches['URL'].get()
                self.CreateGuiReference.SMSSendStandAloneRegion.svURL.set(SMS_gateway_url)
            else:
                pass

        # Add a trace to the entry boxes SMSKey , SMSOriginator , SMS_gateway_url
        for field in self.dictionaryList:
            self.watches[field].trace('w', traceCallback)

        # Button updateSMS parameters creation and callback call
        self.updateSMS = ttk.Button(self.SMSConfigurationFrame, text="Ενημέρωση Υπολοίπου",
                                    command=lambda: self.update_sms(CreateGuiReference, root))
        self.updateSMS.grid(row=(r + 1), column=1, sticky='nsew')

        # The entry field containing the parameters file path
        self.label_load = ttk.Label(self.SMSConfigurationFrame, text="Επιλεγμένο αρχείο:")
        self.label_load.grid(row=(r + 1), column=0, sticky='w')

        self.entry_load_path = ttk.Entry(self.SMSConfigurationFrame, width=30, state='disable')
        self.entry_load_path.grid(row=(r + 2), column=0, sticky='ew')

        # Button load parameters creation and callback call
        self.load = ttk.Button(self.SMSConfigurationFrame,
                               text='Φόρτωση Παραμέτρων', command=self.load_parameters)
        self.load.grid(row=(r + 2), column=1, sticky='nsew')

        # Button Update parameters creation and callback call
        self.updateParameters = ttk.Button(self.SMSConfigurationFrame,
                                           text='Ενημέρωση Παραμέτρων', command=self.updateParams)
        self.updateParameters.grid(row=(r + 3), column=1, sticky='nsew')

        # Configure elements to allow being resized in case of main window resizing

        for i in range(1, 8):
            self.SMSConfigurationFrame.grid_rowconfigure(i, weight=1)

        for i in range(0, 2):
            self.SMSConfigurationFrame.grid_columnconfigure(i, weight=1)

    '''
    The Update Callback Function: It take the gui elements contents and write the back to a file
    chosen from the user with a format suitable for loaded later
    '''

    def update_sms(self, CreateGuiReference, root):
        # If not all fields are completed

        if self.entryFields[1].get() == '':
            messagebox.showinfo("Μήνυμα Εφαρμογής",
                                "Παρακαλω ελέγξτε αν έχετε συμπληρώσει το πεδίο SMS Center Key Code")
        elif self.entryFields[2].get() == '':
            messagebox.showinfo("Μήνυμα Εφαρμογής",
                                "Παρακαλω ελέγξτε αν έχετε συμπληρώσει το πεδίο SMS Originator")
        elif self.entryFields[3].get() == '':
            messagebox.showinfo("Μήνυμα Εφαρμογής",
                                "Παρακαλω ελέγξτε αν έχετε συμπληρώσει το πεδίο SMS Center URL")
        # Ready to contact SMS Gateway to find out if the is SMS quota available to send
        # A progress bar is created and update to reflect (somehow) the progress
        else:

            progress = ttk.Progressbar(root, orient=HORIZONTAL, length=100, mode='determinate')
            progress.pack(expand=True, fill=BOTH, side=TOP)
            progress.start()
            theRoot.update_idletasks()
            progress['value'] = 20
            theRoot.update_idletasks()
            key = self.entryFields[1].get()
            payload = {
                'key': key,
                'type': 'json'
            }

            progress['value'] = 37  # progress update
            theRoot.update_idletasks()
            '''
            Exception handling for the query of the sms gateway.
            If the parameters are correct and the provider is queried successful then the field 
            SMS Υπολοιπο is updated. 
            If not a couple of messages boxes are throw to allow for the identification of the error

            '''
            try:
                SMS_Balance_URL = SMS_gateway_url + BALANCE_URL
                r = requests.post(SMS_Balance_URL, payload)
                progress['value'] = 95  # progress update
                theRoot.update_idletasks()
                jsonparsed = json.loads(r.text)
                SMSbalance = jsonparsed['balance']
                SMSRemarks = jsonparsed['remarks']
                time.sleep(0.5)
                progress['value'] = 100
                theRoot.update_idletasks()
                self.entryFields[0].config(state='normal')
                self.entryFields[0].delete(0, 'end')
                self.entryFields[0].insert(0, SMSbalance)
                self.entryFields[0].config(state='disable')
                '''
                Should I enable tabs initially or after a successful connection with the SMS Service 
                '''
                # if SMSRemarks == "Success":
                #     gui.enable_tabs()
                progress.stop()
                progress.destroy()

            except requests.exceptions.RequestException as e:
                progress.stop()
                progress.destroy()
                messagebox.showinfo("Μήνυμα Εφαρμογής", "Υπάρχει ένα σφάλμα επικοινωνίας με το SMS Gateway. \n"
                                                        "Παρακαλώ ελέγξτε αν έχετε σύνδεση στο Internet \n"
                                                        "και οτι ο πάροχος λειτουργεί κανονικά.")
                message = "Λεπτομέρειες σφάλματος: \n" + str(e)
                messagebox.showinfo("Μήνυμα Εφαρμογής", message)

            except json.decoder.JSONDecodeError as json_e:
                progress.stop()
                progress.destroy()
                messagebox.showinfo("Μήνυμα Εφαρμογής", "Υπάρχει ένα σφάλμα στην απάντηση από το SMS Gateway. \n"
                                                        "Παρακαλώ ελέγξτε αν οι ρυθμίσεις για το  \n"
                                                        "SMS Provider URL είναι σωστές και οτι ο πάροχος λειτουργεί κανονικά.")
                message = "Λεπτομέρειες σφάλματος: \n" + str(json_e)
                messagebox.showinfo("Μήνυμα Εφαρμογής", message)





    '''
        The Load Parameters Callback Function: It open a file opener window and allows the users 
        to choose a file containing the parameters. The these parameters are loaded into the 
        GUI elements
        '''

    def load_parameters(self):
        # Parameters to load from the text file
        global SMSKey
        global SMSOriginator
        global SMS_gateway_url
        global SEND_URL
        global HISTORY_URL
        global BALANCE_URL

        fname = filedialog.askopenfilename(initialdir="/", title="Select file",
                                           filetypes=(("txt files", "*.txt"), ("All files", "*.*")))
        try:
            # Open the file chosen
            file_handler = open(fname, 'r')

            # Update the path entry field to allow the user to view what she/he sees
            self.entry_load_path.config(state='normal')
            self.entry_load_path.delete(0, 'end')
            self.entry_load_path.insert(0, fname)
            self.entry_load_path.configure(state='disabled')

            k = 1  # Iterator for the entry fields
            for line in file_handler:

                if k < 4:
                     self.entryFields[k].delete(0, 'end')
                # Stripping from newlines
                line_stripped_from_nl = (line.split('=')[1]).strip('\n').strip('\'').strip('\"')

                if k == 1:
                    SMSKey = line_stripped_from_nl
                    self.entryFields[k].insert(0, SMSKey)
                elif k == 2:
                    SMSOriginator = line_stripped_from_nl
                    if len(SMSOriginator) > 11:
                        messagebox.showinfo("Μήνυμα Εφαρμογής", "Υπάρχει περιορισμός 11 χαρακτήρων γι' αυτό \n"
                                                                "το πεδίο. Θα κρατηθούν οι πρώτοι 11 χαρακτήρες ")
                        SMSOriginator = SMSOriginator[:11]

                    self.entryFields[k].insert(0, SMSOriginator)
                elif k == 3:
                    SMS_gateway_url = line_stripped_from_nl
                    self.entryFields[k].insert(0, SMS_gateway_url)
                elif k == 4 :
                    SEND_URL = line_stripped_from_nl
                elif k == 5:
                    HISTORY_URL = line_stripped_from_nl
                else:
                    BALANCE_URL = line_stripped_from_nl
                k = k + 1
        except OSError:
            messagebox.showinfo("Μήνυμα Εφαρμογής", "Παρακαλω επιλέγξτε ένα αρχείο για άνοιγμα.")
        except:
            messagebox.showinfo("Μήνυμα Εφαρμογής", "Παρακαλώ ελέγξτε την σωστή μορφή του αρχείου.")
            self.entry_load_path.config(state='normal')
            self.entry_load_path.delete(0, 'end')
            self.entry_load_path.configure(state='disabled')

    '''
        The Update Parameters Callback Function: It take the gui elements contents and write the back to a file
        chosen from the user with a format suitable for loaded later
        '''

    def updateParams(self):
        key = self.entryFields[1].get()
        origin = self.entryFields[2].get()
        url = self.entryFields[3].get()
        # Save as options
        options = {'defaultextension': ".txt"}
        filetypes = [("Text Files", ".txt"), ("All Files", ".*")]
        options['filetypes'] = filetypes
        options['title'] = "Αποθήκευση Παραμέτρων"

        if len(key) == 0 or len(origin) == 0 or len(url) == 0:
            messagebox.showinfo("Μήνυμα Εφαρμογής", "Παρακαλω ελέγξτε αν έχετε συμπληρώσει σωστά τα πεδία...")

        else:
            f = filedialog.asksaveasfile(mode='w', **options)
            if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
                return
            text2save = 'key="' + key + '"\n' + 'origin="' + origin + '"\n' + 'url="' + url + '"' + '"\n'

            ############################################################################
            #######################    HARDCODED VALUE OF THE SMS GATEWAY PROVIDER ######
            send_url = 'sms/send'
            history_url = 'history/single/list'
            balance_url = 'me/balance'
            other_params= 'send_url="' + send_url + '"\n' + 'history_url="' + history_url \
                          + '"\n' + 'balance_url="' + balance_url + '"'
            text2save = str(text2save+other_params)
            f.write(text2save)
            f.close()


'''
#######################################################################
The definition of the class performing the validation and the size limit
of the entry fields for the mobile phone

Code snippet from user: Novel at StackOverflow
## modified to make and length management in my case
######################################################################
'''


class ProxyEntry(ttk.Entry):
    '''A Entry widget that only accepts digits'''

    def __init__(self, master, **kwargs):
        self.var = StringVar()
        self.var.trace('w', self.validate_proxy)
        ttk.Entry.__init__(self, master, textvariable=self.var, **kwargs)
        self.get, self.set = self.var.get, self.var.set

    def validate_proxy(self, *args):
        value = self.get()
        if not value.isdigit():
            self.set(''.join(x for x in value if x.isdigit()))
        if len(value) > 10:
            self.set(self.get()[:10])


'''
#######################################################################
The definition of the class for the tab named 'Αποστολή μεμονωμένου SMS'
######################################################################
'''


class SMSSendStandAlone:
    def __init__(self, SMSSendStandAloneContainer, root):
        # Gui Creation

        self.smsCounter = StringVar()
        self.smsMessagePrint = StringVar(value='160')

        self.svCode = StringVar(value="Δεν υπάρχει")
        self.svOrigin = StringVar(value="Δεν υπάρχει")
        self.svURL = StringVar(value="Δεν υπάρχει")
        # GUI creation with the labels and Entry widgets
        self.smsTitlesFrame = ttk.Frame(SMSSendStandAloneContainer)
        self.smsTitlesFrame.pack(fill=BOTH, expand=1)

        self.smsRegionFrame = ttk.Frame(SMSSendStandAloneContainer)
        self.smsRegionFrame.pack(fill=BOTH, expand=1)

        self.buttonRegion = ttk.Frame(SMSSendStandAloneContainer)
        self.buttonRegion.pack(fill=BOTH, expand=1)

        # The Title label
        self.title_label = ttk.Label(self.smsTitlesFrame, text="Αποστολή μεμονωμένου SMS", font=("Courier", 19),
                                     background='yellow')
        self.title_label.pack(pady=10)
        self.label_sms_center_code_label = ttk.Label(self.smsTitlesFrame, text="SMS Key:", background='#d3d3d3')
        self.label_sms_center_code_label.pack(side=LEFT)
        self.label_sms_center_code_entry = ttk.Label(self.smsTitlesFrame, background='#d3d3d3',
                                                     width=len(self.svCode.get()), textvariable=self.svCode)
        self.label_sms_center_code_entry.pack(side=LEFT, padx=10)

        self.label_sms_center_origin_label = ttk.Label(self.smsTitlesFrame, text="SMS Originator:",
                                                       background='#90ee90')
        self.label_sms_center_origin_label.pack(side=LEFT)
        self.label_sms_center_origin_entry = ttk.Label(self.smsTitlesFrame,
                                                       width=len(self.svOrigin.get()), textvariable=self.svOrigin,
                                                       background='#90ee90')
        self.label_sms_center_origin_entry.pack(side=LEFT, padx=10)

        self.label_sms_center_url_label = ttk.Label(self.smsTitlesFrame, text="SMS Center Url:", background='cyan')
        self.label_sms_center_url_label.pack(side=LEFT)
        self.label_sms_center_url_entry = ttk.Label(self.smsTitlesFrame,
                                                    width=len(self.svURL.get()), textvariable=self.svURL,
                                                    background='cyan')
        self.label_sms_center_url_entry.pack(side=LEFT, padx=10)

        self.labelCharCounterSMS = ttk.Label(self.smsTitlesFrame, text="Χαρακτήρες που απομένουν:")
        self.labelCharCounterSMS.pack()
        self.CharCounterSMS = ttk.Label(self.smsTitlesFrame,
                                        textvariable=self.smsMessagePrint, font=("Helvetica", 14), foreground='red')
        self.CharCounterSMS.pack()

        self.labelMobile = ttk.Label(self.smsRegionFrame, text="Αριθμός Κινητού:")
        self.labelMobile.grid(row=1, column=0, sticky='w')
        self.labelSMS = ttk.Label(self.smsRegionFrame, text="Κείμενο SMS:")
        self.labelSMS.grid(row=2, column=0, sticky='w')
        self.labelLog = ttk.Label(self.smsRegionFrame, text="SMS Log")
        self.labelLog.grid(row=3, column=0, sticky='nsew', pady=5)

        self.mobile = ProxyEntry(self.smsRegionFrame, width=5)

        # The tooltip creation for the aforementioned field
        only_numbers = CreateToolTip(self.mobile, "To πεδίο απαιτεί μόνο αριθμούς")

        self.message = Text(self.smsRegionFrame, width=30, height=10, wrap="word")
        self.mobile.grid(row=1, column=1, sticky='w', pady=5, ipadx=100, ipady=5)
        self.message.grid(row=2, column=1, sticky='nsew', pady=5)
        self.message.bind("<KeyRelease>", self.updateLabel)
        self.message.bind("<KeyPress>", self.updateLabel)

        self.messageLog = Text(self.smsRegionFrame, state='disabled', width=40, height=2, wrap="word", bg="#d3d3d3")
        self.messageLog.grid(row=3, column=1, sticky='nsew', pady=5)

        # Configure elements to allow being resized in case of main window resizing
        self.smsRegionFrame.grid_rowconfigure(0, weight=0)
        self.smsRegionFrame.grid_columnconfigure(0, weight=0)
        self.smsRegionFrame.grid_rowconfigure(1, weight=1)
        self.smsRegionFrame.grid_columnconfigure(1, weight=1)

        # Style definition for allowing a green color button title for easier usage
        self.style = ttk.Style()
        self.style.configure("BW.TButton", foreground="red", background="green")

        # Send SMS button to trigger the send_sms() callback function
        self.send = ttk.Button(self.buttonRegion, text="Send Sms", command=self.send_sms, style='BW.TButton')
        self.send.pack(fill=BOTH, expand=1)

        # Close button to destroy the root window
        self.exit_ = ttk.Button(self.buttonRegion,
                                text='Έξοδος', command=lambda: self.close_window(root))
        self.exit_.pack(fill=BOTH, expand=1)

    '''
    SMS send function: 
    This function performs: a) The check if there is a key,origin and url 
                                parameters available in order to contact the SMS Gateway
                            b) The preparation of the message
                            c)  The sending of the message with the use of the Requests library
                            d) The checking of the response
                            e) The update of all the necessary fields
    '''

    def send_sms(self):

        # Are all the necessary parameters for contacting the SMS Gateway provider are in place?
        if not (bool(SMSKey) and bool(SMSOriginator) and bool(SMS_gateway_url)):
            messagebox.showinfo("Μήνυμα Εφαρμογής", "Δεν έχετε εισάγει τις αναγκαίες παραμέτρους \n"
                                                    "στην καρτέλλα: Παράμετροι κέντρου SMS")
        elif self.mobile.get() == '' or self.message.get("1.0", "end-1c") == '':
            messagebox.showinfo("Μήνυμα Εφαρμογής", "Δεν έχετε εισάγει αριθμό τηλεφώνο είτε έχετε κενό το μήνυμα")
        # Now ready to send...
        else:
            mobile = self.mobile.get()
            payload = {
                'key': SMSKey,
                'text': self.message.get("1.0", "end-1c"),
                'to': mobile,
                'type': 'json',
                'from': SMSOriginator}

            # Sending the SMS through and HTTP post method
            SMS_gateway_url_send = SMS_gateway_url + SEND_URL
            r = requests.post(SMS_gateway_url_send, payload)
            # Parsing the response
            r_json = r.json()
            # Getting the answer fields from the sms gateway services provider
            status = r_json['status']
            balance = r_json['balance']
            remarks = r_json['remarks']
            error = r_json['error']
            smsId = r_json['id']

            if status == '0' and error != '0':
                messagebox.showinfo("Μήνυμα Εφαρμογής", "Εμφανίστηκε πρόβλημα κατά την αποστολή του SMS. \n"
                                                        "Το μήνυμα με παραλήπτη" + str(mobile) + " δεν παραδόθηκε!")
            if status == '1':
                self.messageLog.config(state='normal')
                self.messageLog.delete('1.0', END)
                message = "Το μήνυμα με παραλήπτη " + str(
                    mobile) + " παραδόθηκε επιτυχώς!" + " SMS id = " + smsId + '\n'
                self.messageLog.insert(END, message)
                self.messageLog.config(state='disabled')

    '''
    Function containing the logic for the QUIT Button
    '''

    def close_window(self, root):
        root.destroy()

    '''
      Monitor characters entered in SMS text box in order to limit for the sms limit
      The label is constantly updating
'''

    def updateLabel(self, event):
        value = ''
        self.smsCounter.set(str(len(self.message.get("1.0", 'end-1c'))))
        value = (160 - int(self.smsCounter.get()))
        if value < 0:
            self.message.delete('%s - 2c' % 'end')
            value = (160 - int(str(len(self.message.get("1.0", 'end-1c')))))

        value = str(value)
        self.smsMessagePrint.set('Απομένουν: ' + value + ' χαρακτήρες.')


class popupWindow(object):
    def __init__(self, master, action, treeviewref):
        self.action = action
        self.edit_obj = treeviewref
        if self.action in ['add', 'edit']:
            self.top =  Toplevel(master)
            self.top.geometry("%dx%d%+d%+d" % (400, 400, 350, 225))
            self.top.title("Προσθήκη/Επεξεργασία εγγραφής")
            self.l = Label(self.top, text="Παρακαλώ ενημερώστε τα πεδία \n\n")
            self.l.grid(row=0)
            self.afm_label = Label(self.top, text="ΑΦΜ:")
            self.afm_label.grid(row=1, column=0)
            self.afm = Entry(self.top)
            self.afm.grid(row=1, column=1)

            self.name_label = Label(self.top, text="Όνομα:")
            self.name_label.grid(row=2, column=0)
            self.name = Entry(self.top)
            self.name.grid(row=2, column=1)

            self.surname_label = Label(self.top, text="Επώνυμο:")
            self.surname_label.grid(row=3, column=0)
            self.surname = Entry(self.top)
            self.surname.grid(row=3, column=1)

            self.fathersname_label = Label(self.top, text="Πατρώνυμο:")
            self.fathersname_label.grid(row=4, column=0)
            self.fathersname = Entry(self.top)
            self.fathersname.grid(row=4, column=1)

            self.mobile_label = Label(self.top, text="Κινητό:")
            self.mobile_label.grid(row=5, column=0)
            self.mobile = Entry(self.top)
            self.mobile.grid(row=5, column=1)

            self.other_label = Label(self.top, text="Λοιπά Στοιχεία:")
            self.other_label.grid(row=6, column=0)
            self.other = Entry(self.top)
            self.other.grid(row=6, column=1)
            #Allow on one window to appear on multiple add clicks
            self.top.transient()
            self.top.grab_set()



            if self.action == "add":
                self.ButtonsFrame = ttk.Frame(self.top)
                self.ButtonsFrame.grid(row=7, column=1, sticky="nsew")
                self.add = Button(self.ButtonsFrame, text='Προσθήκη', command=lambda: self.add_or_edit("add",-1))
                self.add.grid(row=0, column=0)
                self.cancel = Button(self.ButtonsFrame, text='Cancel', command=self.cleanup)
                self.cancel.grid(row=0, column=1)


            elif self.action == "edit":

                field_list = [self.afm , self.surname ,self.name , self.mobile ,self.fathersname,  self.other]
                #get the record id
                self.id = self.edit_obj[6]
                self.ButtonsFrame = ttk.Frame(self.top)
                self.ButtonsFrame.grid(row=7, column=1, sticky="nsew")
                self.add = Button(self.ButtonsFrame, text='Ενημέρωση', command=lambda: self.add_or_edit("edit",self.id))
                self.add.grid(row=0, column=0)
                self.cancel = Button(self.ButtonsFrame, text='Cancel', command=self.cleanup)
                self.cancel.grid(row=0, column=1)
                self.id = self.edit_obj[6]
                for i, field in enumerate(field_list):
                    field.insert(0, self.edit_obj[i])

        else:
            MsgBox = messagebox.askquestion('Διαγραφή Στοιχείων',
                                            'Είστε σίγουροι ότι θέλετε να διαγράψετε την εγγραφή?',
                                            icon='question')
            if MsgBox == 'yes':
                newMsg = messagebox.showinfo('Διαγραφή Στοιχείων', 'Η εγγραφή διαγράφηκε!', icon='warning')
            else:
                pass

    def add_or_edit(self, action,id):

        # Add or Edit
        self.action = action
        # Get the ID to edit
        if id != -1:
            self.id=id

        self.afm_value = self.afm.get()
        self.name_value = self.name.get()
        self.surname_value = self.surname.get()
        self.fathersname_value = self.fathersname.get()
        self.mobile_value = self.mobile.get()
        self.other_value = self.other.get()

        list_of_values = [self.afm_value, self.name_value, self.surname_value, self.fathersname_value,
                          self.mobile_value,
                          self.other_value]
        # Do not insert empty values
        if '' not in list_of_values:
            if messagebox.askyesno('Μήνυμα Εφαρμογής', 'Συμφωνείτε με την εισαγωγή/επεξεργασία ?', parent=self.top):
                db_object = DatabaseHandler()
                db_object.create_db()
                if self.action == "add":
                    db_object.insert(self.afm_value, self.name_value, self.surname_value,
                                 self.fathersname_value, self.mobile_value, self.other_value)
                elif self.action == "edit":
                    db_object.update(self.id, self.afm_value, self.name_value, self.surname_value,
                                     self.fathersname_value, self.mobile_value, self.other_value)
                else:
                    messagebox.showinfo("Μήνυμα Εφαρμογής", "Εμφανίστηκε ένα σφάλμα λειτουργίας. Παρακαλώ επικοινωνήστε"
                                                            "με τον διαχειριστή.")


                db_object.close_connection()
                self.cleanup()
        else:
            messagebox.showinfo('Μήνυμα Εφαρμογής', 'Παρακαλώ ελέγξτε αν όλα τα πεδία της φόρμας είναι συμπληρωμένα.',
                                parent=self.top)


    def cleanup(self):
        self.top.destroy()


class SMSSendTeachers:

    def __init__(self, SMSSendTeachersContainer, root):

        self.root = root
        self.value = ''
        self.Label = []
        self.smsCounter = StringVar()
        self.smsMessagePrint = StringVar()
        self.SMSSendTeachersFrame = ttk.Frame(SMSSendTeachersContainer)
        self.SMSSendTeachersFrame.pack(fill=BOTH, expand=1)

        self.csvContent = ttk.Frame(SMSSendTeachersContainer)
        self.csvContent.pack(fill=BOTH, expand=1)

        self.smsSelectedNumbersFrame = ttk.Frame(SMSSendTeachersContainer)
        self.smsSelectedNumbersFrame.pack(fill=BOTH, expand=1)

        self.smsRegionFrame = ttk.Frame(SMSSendTeachersContainer)
        self.smsRegionFrame.pack(fill=BOTH, expand=1)

        self.label = ttk.Label(self.SMSSendTeachersFrame, text="Αποστολή μηνυμάτων σε εκπαιδευτικούς ",
                               font=("Courier", 19), background='yellow')
        self.label.grid(row=0, columnspan=3, pady=10)
        self.entryFields = []

        self.SMSSendTeachersFrame.grid_rowconfigure(0, weight=1)
        self.SMSSendTeachersFrame.grid_columnconfigure(0, weight=1)
        self.SMSSendTeachersFrame.grid_rowconfigure(1, weight=1)
        self.SMSSendTeachersFrame.grid_columnconfigure(1, weight=1)
        self.SMSSendTeachersFrame.grid_rowconfigure(2, weight=1)
        self.photo_refresh = PhotoImage(file=r"./icons/refresh.png")

        self.refresh = ttk.Button(self.SMSSendTeachersFrame, text='Refresh', image=self.photo_refresh,
                                  compound=LEFT, command=self.load_from_sqlite).grid(row=2, column=5, sticky='ns')

        self.photo_edit = PhotoImage(file=r"./icons/edit.png")
        self.edit = ttk.Button(self.SMSSendTeachersFrame, text='Edit', image=self.photo_edit,
                               compound=LEFT, command=self.edit_from_sqlite).grid(row=2, column=4, sticky='ns')

        self.photo_add = PhotoImage(file=r"./icons/add.png")
        self.add = ttk.Button(self.SMSSendTeachersFrame, text='Add', image=self.photo_add,
                              compound=LEFT, command=self.add_to_sqlite).grid(row=2, column=2, sticky='ns')
        self.photo_del = PhotoImage(file=r"./icons/del.png")

        self.delete = ttk.Button(self.SMSSendTeachersFrame, text='Del', image=self.photo_del,
                                 compound=LEFT, command=self.del_from_sqlite).grid(row=2, column=3, sticky='ns')

        self.tree = ttk.Treeview(self.csvContent, columns=("afm", "surname", "name", "mobile", "fathersname", "other"))
        self.tree.heading('afm', text="ΑΦΜ", anchor=W)

        self.tree.heading('surname', text="Επώνυμο", anchor=W)
        self.tree.heading('name', text="Όνομα", anchor=W)
        self.tree.heading('mobile', text="Κινητό Τηλέφωνο", anchor=W)
        self.tree.heading('fathersname', text="Πατρώνυμο", anchor=W)

        self.tree.heading('other', text="Πληροφορίες", anchor=W)
        self.tree.column('#0', stretch=NO, minwidth=0, width=0)
        self.tree.column('#1', stretch=NO, minwidth=0, width=100)
        self.tree.column('#2', stretch=NO, minwidth=0, width=180)
        self.tree.column('#3', stretch=NO, minwidth=0, width=150)
        self.tree.column('#4', stretch=NO, minwidth=0, width=150)
        self.tree.column('#5', stretch=NO, minwidth=0, width=180)
        self.tree.pack(fill=BOTH, expand=1)
        self.tree.bind("<ButtonRelease-1>", self.OnClick)

        self.labelSelectedSMS = ttk.Label(self.smsSelectedNumbersFrame, text="Επιλεγμένοι Αριθμοί")
        self.labelSelectedSMS.grid(row=0, column=0, sticky='nsew')

        self.selectedtree = ttk.Treeview(self.smsSelectedNumbersFrame, height=4, columns=("surname", "name", "mobile"))
        self.selectedtree.heading('surname', text="Επώνυμο", anchor=W)
        self.selectedtree.heading('name', text="Όνομα", anchor=W)
        self.selectedtree.heading('mobile', text="Κινητό Τηλέφωνο", anchor=W)
        self.selectedtree.column('#0', stretch=NO, minwidth=0, width=0)
        self.selectedtree.column('#1', stretch=NO, minwidth=0, width=200)
        self.selectedtree.column('#2', stretch=NO, minwidth=0, width=200)
        self.selectedtree.grid(row=1, column=0, sticky='nsew')

        self.labelCharCounterSMS = ttk.Label(self.smsSelectedNumbersFrame, text="Χαρακτήρες που απομένουν:")
        self.labelCharCounterSMS.grid(row=0, column=1, sticky='nsew')

        self.CharCounterSMS = ttk.Label(self.smsSelectedNumbersFrame,
                                        textvariable=self.smsMessagePrint, font=("Helvetica", 14), foreground='red')
        self.CharCounterSMS.grid(row=1, column=1, sticky='nsew')

        self.labelSMS = ttk.Label(self.smsRegionFrame, text="SMS to Send")
        self.labelSMS.grid(row=0, column=0, sticky='nsew')

        self.message = Text(self.smsRegionFrame, width=30, height=10, wrap="word")
        self.message.grid(row=1, column=0, sticky='nsew')
        self.message.bind("<KeyRelease>", self.updateLabel)
        self.message.bind("<KeyPress>", self.updateLabel)

        self.labelLog = ttk.Label(self.smsRegionFrame, text="SMS Log")
        self.labelLog.grid(row=0, column=1, sticky='nsew')
        self.messageLog = Text(self.smsRegionFrame, state='disabled', width=40, height=10, wrap="word", bg="#d3d3d3")
        self.messageLog.grid(row=1, column=1, sticky='nsew')

        self.send = ttk.Button(self.smsRegionFrame, text="Send SMS", command=self.send_sms)
        self.send.grid(row=1, column=2, sticky='nsew')

        for i in range(0, 2):
            self.smsRegionFrame.grid_rowconfigure(i, weight=1)

        for i in range(0, 3):
            self.smsRegionFrame.grid_columnconfigure(i, weight=1)

        self.load_from_sqlite()

    '''
        Add record to sqlite database
    '''

    def add_to_sqlite(self):
        self.w = popupWindow(self.root, "add", None)
        self.root.wait_window(self.w.top)
        self.load_from_sqlite()

    '''
            Edit record from sqlite database
        '''

    def edit_from_sqlite(self):

        tree_items = self.tree.selection()
        if (len(tree_items)) > 1:
            messagebox.showwarning("Μήνυμα εφαρμογής", "Επιλέξτε μόνο μία εγγραφή \n για τη λειτουργία  "
                                                       "της Επεξεργασίας")
            self.tree.selection_set()
            self.selectedtree.delete(*self.selectedtree.get_children())

        elif (len(tree_items)) == 0:
            messagebox.showinfo("Μήνυμα Εφαρμογής", "Θα πρέπει πρώτα να επιλέξετε μία εγγραφή!")
        else:
            curItem = self.tree.focus()

            self.w = popupWindow(self.root, "edit", self.tree.item(curItem)['values'])
            self.root.wait_window(self.w.top)
            self.load_from_sqlite()

    '''
            Delete record to sqlite database
        '''

    def del_from_sqlite(self):

        tree_item = self.tree.selection()
        if tree_item:

            if messagebox.askyesno('Μήνυμα Εφαρμογής', 'Συμφωνείτε με την διαγραφή'):
                selectedTeachers = []
                db_object = DatabaseHandler()
                for i in tree_item:
                    selectedTeachers.append(self.tree.item(i, "values"))
                for teacher in selectedTeachers:
                    db_object.delete_entry(int(teacher[6]))

                db_object.close_connection()
                self.load_from_sqlite()
                self.selectedtree.delete(*self.selectedtree.get_children())
        else:
            messagebox.showwarning('Μήνυμα Εφαρμογής', 'Παρακαλώ επιλέγξτε τουλάχιστον μια εγγραφή για διαγραφή!')

    '''
      Monitor characters entered in SMS text box in order to limit for the sms limit
      The label is constantly updating
    '''

    def updateLabel(self, event):
        self.smsCounter.set(str(len(self.message.get("1.0", 'end-1c'))))
        self.value = (160 - int(self.smsCounter.get()))
        if self.value < 0:
            self.message.delete('%s - 2c' % 'end')
            self.value = (160 - int(str(len(self.message.get("1.0", 'end-1c')))))

        self.value = str(self.value)
        self.smsMessagePrint.set('Απομένουν: ' + self.value + ' χαρακτήρες.')

    '''
    Main routine to load the CSV file. The File should be correctly formatted as described in the help file
    '''

    def load_from_sqlite(self):
        self.tree.delete(*self.tree.get_children())
        self.selectedtree.delete(*self.selectedtree.get_children())
        try:
            self.conn = sqlite3.connect('teachersDB.db')
            self.cursor = self.conn.cursor()
            self.cursor.execute('SELECT * FROM teachers')
            for row in self.cursor:

                afm = row[1]
                surname = row[2]
                name = row[3]
                fathersname = row[5]
                mobile = row[4]
                other = row[6]
                id = row[0]
                self.tree.insert("", 0, values=(afm, name, surname, fathersname, mobile, other, id))

        except sqlite3.Error as e:

            message = "Παρακαλώ μεταφορτώστε κάποιο αρχείο δεδομένων \n ή \n Εισάγετε εγγραφές στην εφαρμογή \n. \n " \
                      "Λεπτομέρειες Σφάλματος: " + str(e)

        except Exception as e:
            print("Exception in : %s" % e)
        finally:
            self.conn.commit()
            self.conn.close()

    '''
 Insert selected teacher into the selected teacher tree panel.
 Teacher can be selected either one by one or in multiple units
 by pressing Ctrl+Click
  '''

    def OnClick(self, event):
        tree_item = self.tree.selection()
        selectedTeachers = []
        for i in tree_item:
            selectedTeachers.append(self.tree.item(i, "values"))

        selectedTeachers = list(set(selectedTeachers))  # keep unique
        self.selectedtree.delete(*self.selectedtree.get_children())
        for teacher in selectedTeachers:
            self.selectedtree.insert("", index=0, values=[teacher[1], teacher[2], teacher[3]])

    '''
Main routine sending the sms to the selected teachers
    '''

    def send_sms(self):
        self.messageLog.configure(state='normal')
        if len(self.tree.selection()) == 0:
            messagebox.showinfo("Μήνυμα Εφαρμογής", "Δεν έχετε επιλέξει κανένα παραλήπτη...")
        elif not (bool(SMSKey) and bool(SMSOriginator) and bool(SMS_gateway_url)):
            messagebox.showinfo("Μήνυμα Εφαρμογής", "Δεν έχετε εισάγει τις αναγκαίες παραμέτρους \n"
                                                    "στην καρτέλλα: Παράμετροι κέντρου SMS")
        else:
            for index, iid in enumerate(self.tree.selection()):
                mobile = self.tree.item(iid)['values'][3]
                payload = {
                    'key': SMSKey,
                    'text': self.message.get("1.0", "end-1c"),
                    'to': mobile,
                    'type': 'json',
                    'from': SMSOriginator}

                SMS_gateway_url_send = SMS_gateway_url + SEND_URL
                r = requests.post(SMS_gateway_url_send, payload)
                r_json = r.json()
                status = r_json['status']
                balance = r_json['balance']
                remarks = r_json['remarks']
                error = r_json['error']
                smsId = r_json['id']

                if status == '0' and error != '0':
                    messagebox.showinfo("Μήνυμα Εφαρμογής", "Εμφανίστηκε πρόβλημα κατά την Αποστολή. \n"
                                                            "Το μήνυμα με παραλήπτη" + str(mobile) + " δεν παραδόθηκε!")
                if status == '1':
                    message = str(index) + ". Το μήνυμα με παραλήπτη " + str(
                        mobile) + " παραδόθηκε επιτυχώς!" + " SMS id = " + smsId + '\n'
                    self.messageLog.insert(END, message)



class SMSLogFromServer:
    def __init__(self, SMSLogFromServerContainer, root):

        self.SMSLogTitleFrame = ttk.Frame(SMSLogFromServerContainer)
        self.SMSLogTitleFrame.pack(fill=BOTH)

        self.SMSLogContent = ttk.Frame(SMSLogFromServerContainer)
        self.SMSLogContent.pack(fill=BOTH)
        self.SMSLogButtonContent = ttk.Frame(SMSLogFromServerContainer)
        self.SMSLogButtonContent.pack(pady=15)

        self.SMSDetailsContent = ttk.Frame(SMSLogFromServerContainer)
        self.SMSDetailsContent.pack(fill=BOTH, expand=1)

        self.loglabel = ttk.Label(self.SMSLogTitleFrame, text="Αρχείο απεσταλμένων SMS από πάροχο",
                                  font=("Courier", 16), background='yellow')
        self.loglabel.pack(pady=10)

        self.tree = ttk.Treeview(self.SMSLogContent, columns=("SMSId", "sender", "to", "timestamp", "status")
                                 , selectmode="browse")
        self.tree.heading('timestamp', text="Hμερομηνία", anchor=W)
        self.tree.heading('SMSId', text="SMSId", anchor=W)
        self.tree.heading('sender', text="Αποστολέας", anchor=W)
        self.tree.heading('to', text="Παραλήπτης", anchor=W)

        self.tree.heading('status', text="Παραδόθηκε?", anchor=W)

        self.tree.column('#0', stretch=NO, minwidth=0, width=30)
        self.tree.column('#1', stretch=NO, minwidth=0, width=200)
        self.tree.column('#2', stretch=NO, minwidth=0, width=150)
        self.tree.column('#3', stretch=NO, minwidth=0, width=150)
        self.tree.column('#4', stretch=NO, minwidth=0, width=150)
        self.tree.column('#5', stretch=NO, minwidth=0, width=90)
        self.tree.pack()
        self.loadButton = ttk.Button(self.SMSLogButtonContent,
                                     text="Φόρτωση Δεδομένων", command=lambda: self.fetch_data(root))

        self.loadButton.pack(expand=1, fill=BOTH, ipady=20, ipadx=20)
        self.DetailsTextLabel = ttk.Label(self.SMSDetailsContent, text="Λεπτομέρειες Μηνύματος:")
        self.DetailsTextLabel.grid(row=0, column=0, sticky='w')
        self.DetailsTextLabel = ttk.Label(self.SMSDetailsContent, text="Λεπτομέρειες Μηνύματος:")
        self.DetailsTextLabel.grid(row=0, column=0, sticky='w')

        self.DetailsText = Text(self.SMSDetailsContent, width=100, height=2, wrap="word", state='disabled')
        self.DetailsText.grid(row=1, column=0, sticky='w')

        self.tree.bind("<ButtonRelease-1>", self.OnClick)

    '''
    Details of the clicked item implementation
    '''

    def OnClick(self, event):
        tree_item = self.tree.selection()
        region = self.tree.identify("region", event.x, event.y)
        if region == "tree":
            pass
        else:

            self.DetailsText.config(state='normal')
            self.DetailsText.delete('1.0', END)

            if len(self.tree.item(tree_item)['values']) == 6:
                self.DetailsText.insert(END, self.tree.item(tree_item)['values'][5])
            else:
                self.DetailsText.insert(END, "Επιλέξτε μήνυμα...")
            self.DetailsText.config(state='disabled')


    def fetch_data(self, root):

        time_stamps_dates_list = []
        if not (bool(SMSKey) and bool(SMSOriginator) and bool(SMS_gateway_url)):
            messagebox.showinfo("Μήνυμα Εφαρμογής", "Δεν έχετε εισάγει τις αναγκαίες παραμέτρους \n"
                                                    "στην καρτέλλα: Παράμετροι κέντρου SMS")
        else:

            progress = ttk.Progressbar(root, orient=HORIZONTAL, length=100, mode='determinate')
            progress.pack(expand=True, fill=BOTH, side=TOP)
            progress.start()
            theRoot.update_idletasks()
            progress['value'] = 20
            theRoot.update_idletasks()

            payload = {
                'key': SMSKey,
                'type': 'json',
            }

            progress['value'] = 37  # progress update
            theRoot.update_idletasks()
            SMS_gateway_url_history = SMS_gateway_url + HISTORY_URL

            try:
                SMS_gateway_url_history = SMS_gateway_url + HISTORY_URL

                r = requests.post(SMS_gateway_url_history, payload)
                progress['value'] = 85  # progress update
                theRoot.update_idletasks()

                r_json = r.json()

                # Create unique timestamps
                # Get dates from json
                for i in r_json['sms']:
                    timestamp_date = i['timestamp'][0:10]
                    time_stamps_dates_list.append(timestamp_date)
                # Convert the to set for uniqueness
                time_stamps_set = set(time_stamps_dates_list)
                # List again to traverse
                time_stamps_dates_list = list(time_stamps_set)
                time_stamps_dates_list.sort(key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
                time.sleep(0.5)
                progress['value'] = 100
                theRoot.update_idletasks()
                progress.stop()
                progress.destroy()

                for dates in time_stamps_dates_list:
                    self.tree.insert('', 'end', dates, values=dates)

                for i in r_json['sms']:
                    SMSId = i['smsId']
                    sender = i['sender']
                    to = i['to']
                    text = i['text']
                    timestamp = i['timestamp']
                    status = i['status']
                    if status == 'd':
                        status = 'Παραδόθηκε'
                    elif status == 'f':
                        status = 'Απέτυχε'
                    else:
                        status = 'Άγνωστο'

                    date_in_to_be_appended = timestamp[0:10]
                    self.tree.insert(str(date_in_to_be_appended), 'end', values=(SMSId, sender, to,
                                                                                 timestamp, status, text))
            except requests.exceptions.RequestException as e:
                progress.stop()
                progress.destroy()
                messagebox.showinfo("Μήνυμα Εφαρμογής", "Υπάρχει ένα σφάλμα επικοινωνίας με το SMS Gateway. \n"
                                                        "Παρακαλώ ελέγξτε αν έχετε σύνδεση στο Internet \n"
                                                        "και οτι ο πάροχος λειτουργεί κανονικά.")
                message = "Λεπτομέρειες σφάλματος: \n" + str(e)
                messagebox.showinfo("Μήνυμα Εφαρμογής", message)




class DatabaseAndCSV:
    def __init__(self, DatabaseContainer, root):
        self.DBTitlesFrame = ttk.Frame(DatabaseContainer)
        self.DBTitlesFrame.pack()

        self.DBbuttonRegionFrame = ttk.Frame(DatabaseContainer)
        self.DBbuttonRegionFrame.pack()
        self.title_label = ttk.Label(self.DBTitlesFrame, text="Διαχείριση αρχείων", font=("Courier", 19),
                                     background='yellow')
        self.title_label.grid(row=0, columnspan=3, pady=10)

        self.send = ttk.Button(self.DBbuttonRegionFrame, text="Εισαγωγή CSV στη βάση δεδομένων",
                               command=self.importCSVtoSqlite, style='BW.TButton')
        self.send.grid(row=0, columnspan=3, pady=10, sticky='ew')
        # self.send = ttk.Button(self.DBbuttonRegionFrame, text="Αποθήκευση Βάσης Δεδομένων", style='BW.TButton')
        # self.send.grid(row=1, columnspan=3, pady=10,sticky='ew')
        self.send = ttk.Button(self.DBbuttonRegionFrame, text="Διαγραφή Βάσης Δεδομένων", command=self.dropTable,
                               style='BW.TButton')
        self.send.grid(row=2, columnspan=3, pady=10, sticky='ew')

    def dropTable(self):
        try:
            db_object = DatabaseHandler()
        except:
            messagebox.showinfo("Μήνυμα Εφαρμογής", "Εμφανίστηκε πρόβλημα κατά την διαδικασία πρόσβασης στην"
                                                    "βάση δεδομένων. Παρακαλώ ελέγχξτε αν έχετε"
                                                    "επαρκή χώρο στο δίσκο σας.")

        MsgBox = messagebox.askquestion('Διαγραφή Στοιχείων',
                                        'Είστε σίγουροι ότι θέλετε να διαγράψετε την βάση δεδομένων!',
                                        icon='warning')
        if MsgBox == 'yes':
            newMsg = messagebox.askquestion('Διαγραφή Στοιχείων', 'Επιμένετε?', icon='warning')
            if newMsg == 'yes':
                result = db_object.drop()
                db_object.close_connection()

                message = "Λεπτομέρειες Μηνύματος: \n" + str(result)
                newMsg = messagebox.showinfo('Διαγραφή Στοιχείων', message, icon='warning')
        else:
            pass

    def importCSVtoSqlite(self):

        try:
            db_object = DatabaseHandler()
        except:
            messagebox.showinfo("Μήνυμα Εφαρμογής", "Εμφανίστηκε πρόβλημα κατά την διαδικασία πρόσβασης στην"
                                                    "βάση δεδομένων. Παρακαλώ ελέγχξτε αν έχετε"
                                                    "επαρκή χώρο στο δίσκο σας.")
        fname = filedialog.askopenfilename(initialdir="/", title="Επιλέγξτε αρχείο...",
                                           filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))

        try:
            with open(fname, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                db_object.create_db()

                for row in reader:
                    afm = row['afm']
                    surname = row['surname']
                    name = row['name']
                    fathersname = row['fathersname']
                    mobile = row['mobile']
                    other = row['other']
                    db_object.insert(afm, name, surname, fathersname, mobile, other)
                messagebox.showinfo("Μήνυμα Εφαρμογής", "H εισαγωγή των στοιχείων έγινε επιτυχώς")
                db_object.close_connection()

        except OSError:
            messagebox.showinfo("Μήνυμα Εφαρμογής", "Παρακαλώ επιλέγξτε ένα αρχείο για άνοιγμα.")
        except Exception as e:
            print(e)

            messagebox.showinfo("Μήνυμα Εφαρμογής", "To αρχείο δεν έχει την σωστή μορφή...")


class DeveloperRegion:
    def __init__(self, DeveloperContainer, root):
        self.style = ttk.Style()
        self.style.configure('Header.TLabel', font=('Arial', 18, 'bold'))
        self.style.configure('Header.Custom', font=('Arial', 15, 'bold'))

        def callback(url):
            webbrowser.open_new(url)

        self.DeveloperFrame = ttk.Frame(DeveloperContainer)
        self.DeveloperFrame.pack()  # fill=BOTH, expand=1
        self.title_label = ttk.Label(self.DeveloperFrame, text="Σχετικά με την εφαρμογή", font=("Courier", 19),
                                     background='yellow')
        self.title_label.pack(pady=10)

        ttk.Label(self.DeveloperFrame, text='Εφαρμογή Αποστολής SMS', style='Header.TLabel').pack(pady=10)
        ttk.Label(self.DeveloperFrame, wraplength=400,
                  text=(
                      "H εφαρμογή αποτελεί τη συνέχεια της εφαρμογής που αναπτύχθηκε το 2018/2019 με βάση τις τεχνολογίες "
                      "PHP / MySQL / Javascript / BootStrap \n και είναι διαθέσιμη στο Github. "
                      "Αναδημιουργήθηκε ως Desktop εφαρμογή με τη χρήση της Python και του Tkinter που αποτελεί "
                      "ένα object-oriented layer για την Tcl/Tk. \n \n"
                      "H εφαρμογή είναι δωρεάν και χωρίς κανένα περιορισμό στη χρήση και τροποποίηση της. "
                      "Δημιουργήθηκε μόνο ως προσφορά στην κοινότητα και ως μια μικρή βοήθεια σπό μέρους μου για την "
                      "ακόμα μεγαλύτερη προσέγγιση στην ηλεκτρονική δημοκρατία. "
                      "H χρήση της γίνεται με πλήρη την ευθύνη του κάθε ενδιαφερόμενου και χωρίς να δίνεται καμία εγγύηση"
                      " καλής λειτουργίας. \n\n"
                      "Άδεια: GPLv3 \n\n"
                      "Δημιουργός: Κωνσταντίνος Χερτούρας \n \n"
                      "Διπλωματούχος Σχολής ΗΜΜΥ Πολυτεχνείου Κρήτης, 1998 \n"
                      "ΜSc ECE Imperial College London, 1999 \n"
                      "ΜSc Πληροφορική Σχολή ΗΜΜΥ, ΑΠΘ 2006 \n\n"
                      "Amazon Web Services Certified Solutions Architect - Associate \n"
                      "Microsoft Expert Excel 2016 - Interpreting Data for Insights \n\n"
                      "e-mail: chertour@sch.gr"

                  )).pack()
        self.photo_linked_in = PhotoImage(file=r"./icons/linkedin.png")
        self.photo_github = PhotoImage(file=r"./icons/GitHub-Mark-32px.png")
        self.photo_aws = PhotoImage(file=r"./icons/aws.png")
        Link_aws = Label(self.DeveloperFrame, text=" \n", fg="blue", image=self.photo_aws,
                         cursor="hand2", compound=LEFT)
        Link_aws.pack()
        Link_aws.bind("<Button-1>", lambda e: callback(
            "https://www.certmetrics.com/amazon/public/badge.aspx?i=1&t=c&d=2018-03-27&ci=AWS00398857"))
        link_linked_in = Label(self.DeveloperFrame, text="\n", fg="blue", image=self.photo_linked_in,
                               cursor="hand2", compound=LEFT)
        link_linked_in.pack()
        link_linked_in.bind("<Button-1>", lambda e: callback("https://www.linkedin.com/in/chertouras/"))
        link_github = Label(self.DeveloperFrame, text=" ", fg="blue",
                            image=self.photo_github, cursor="hand2", compound=LEFT)
        link_github.pack()
        link_github.bind("<Button-1>", lambda e: callback("https://github.com/chertouras"))


class CreateGui:

    def __init__(self, root):


        root.title('Σύστημα Αποστολής SMS')

        root.configure(background='#e1d8b9')
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=BOTH, expand=1)
        self.SMSNetworkParamsContainer = ttk.Frame(self.notebook, width=490, height=490)
        self.SMSSendStandAloneContainer = ttk.Frame(self.notebook, width=490, height=490)
        self.SMSSendTeachersContainer = ttk.Frame(self.notebook, width=490, height=490)
        self.SMSLogFromServerContainer = ttk.Frame(self.notebook, width=490, height=490)
        self.DeveloperContainer = ttk.Frame(self.notebook, width=490, height=490)
        self.DatabaseContainer = ttk.Frame(self.notebook, width=490, height=490)
        self.notebook.add(self.SMSNetworkParamsContainer, text='Παράμετροι κέντρου SMS')
        self.notebook.add(self.SMSSendStandAloneContainer, text='Αποστολή μεμονωμένου SMS')
        self.notebook.add(self.SMSSendTeachersContainer, text='Αποστολή SMS σε εκπαιδευτικούς')
        self.notebook.add(self.SMSLogFromServerContainer, text='Αρχείο απεσταλμένων SMS')
        self.notebook.add(self.DatabaseContainer, text='Διαχείριση αρχείων')
        self.notebook.add(self.DeveloperContainer, text='Σχετικά με την εφαρμογή')

        self.SMSNetworkRegion = SMSConfiguration(self.SMSNetworkParamsContainer, self, root)
        self.SMSSendTeachersRegion = SMSSendTeachers(self.SMSSendTeachersContainer, root)
        self.SMSSendStandAloneRegion = SMSSendStandAlone(self.SMSSendStandAloneContainer, root)
        self.SMSLogFromServerRegion = SMSLogFromServer(self.SMSLogFromServerContainer, root)
        self.DatabaseRegion = DatabaseAndCSV(self.DatabaseContainer, root)
        self.DeveloperRegion = DeveloperRegion(self.DeveloperContainer, root)


class DatabaseHandler:
    def __init__(self):
        try:
            self.conn = sqlite3.connect('teachersDB.db')
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print("Database error: %s" % e)
        except Exception as e:
            print("Exception in : %s" % e)
        finally:
            pass

    def create_db(self):

        try:
            self.cursor.execute('CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY AUTOINCREMENT,afm INTEGER,'
                                'name TEXT,surname TEXT,fathersname TEXT,mobile TEXT,other TEXT)')

        except sqlite3.Error as e:
            print("Database error: %s" % e)
        except Exception as e:
            print("Exception in : %s" % e)
        finally:
            pass

    def drop(self):
        try:
            query = '''DROP TABLE IF EXISTS teachers'''
            self.conn.execute(query)

        except sqlite3.Error as e:
            return str(e)
        finally:
            pass

    def delete_entry(self, id):
        query = '''DELETE from teachers where id = ? '''
        self.cursor.execute(query, (id,))

    def insert(self, afm, name, surname, fathersname, mobile, other):
        query = '''INSERT INTO teachers( afm, name, surname, fathersname, mobile, other ) VALUES ( ?,?,?,?,?,? ) '''
        self.cursor.execute(query, (afm, name, surname, fathersname, mobile, other))

    def update(self, id, afm, name, surname, fathersname, mobile, other):
        query = '''UPDATE teachers SET  afm= ? , name=? , surname=? , fathersname=? , mobile=?, other=?  
            WHERE id=? '''
        self.cursor.execute(query, (afm, name, surname, fathersname, mobile, other,id))


    def close_connection(self):
        try:
            self.conn.commit()
            self.conn.close()
        except sqlite3.Error as e:
            return str(e)
        finally:
            pass


class SMSSenderClass:
    def __init__(self, root):
        pass

'''
The splash screen
'''

class SplashScreen:
    root = Tk()
    #Hide the border
    root.overrideredirect(True)

    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()

    root.geometry('%dx%d+%d+%d' % (width * 0.7, height * 0.7, width * 0.1, height * 0.1))

    image_file = "images/splash.png"
    imageopen = Image.open(image_file)
    image = ImageTk.PhotoImage(imageopen)
    canvas = Canvas(root, height=height * 0.7, width=width * 0.7, bg="brown")
    canvas.create_image(width * 0.7 / 2, height * 0.7 / 2, image=image)
    canvas.pack()

    root.after(2300, root.destroy)
    root.mainloop()

'''
The main entry point

'''
def main():

    global theRoot
    root = Tk()
    theRoot = root
    sp = SplashScreen()
    gui = CreateGui(root)
    root.mainloop()


if __name__ == "__main__": main()
