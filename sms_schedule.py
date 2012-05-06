#+-----------------------------------------------------+
# 			Includes 
#+-----------------------------------------------------+

import appuifw
import e32
import contacts
from time import *
import messaging
import os
from key_codes import *
from e32db import format_time

#+------------------------------------------------------+
# 			Global variables 
#+------------------------------------------------------+

AppLock = e32.Ao_lock()
ScheduledSMSList = []
HistorySMSList = []
Contacts = []
SessionConfigFileIDStr = 'SMSScheduler session config file'
SessionConfigFileVersion = 1.2
Timer = e32.Ao_timer()
ToolTip = appuifw.InfoPopup()
TabIndex = 0;

#+------------------------------------------------------+
# 			Classes
#+------------------------------------------------------+

class SMS:
	Contacts = []
	Message = ''
	Date = 0
	Time = 0
	Repeat = 0
	Send = False

#+------------------------------------------------------+
#			 Functions 
#+------------------------------------------------------+

#+------------------------------------------------------+
#			schedule sms
#+------------------------------------------------------+

def AddEditScheduledSMS(EditScheduledSMS):
	if EditScheduledSMS:
		appuifw.app.title = u'Edit scheduled SMS'
	else:
		appuifw.app.title = u'Schedule new SMS'
		
	Message = u''
	Date = time()
	Time = float(12 * 60 * 60)
	Repeat = 0
	
	if EditScheduledSMS:
		Message = EditScheduledSMS.Message
		Date = EditScheduledSMS.Date
		Time = EditScheduledSMS.Time
		Repeat = EditScheduledSMS.Repeat

	Message = appuifw.query(u'Enter message', 'text', Message)
	
	if Message != None:
		Date = appuifw.query(u'Enter send date', 'date', Date)
		
		if Date != None:
			Time = appuifw.query(u'Enter send time', 'time', Time)
			
			if Time != None:
				Repeat = appuifw.selection_list([u'Never', u'Hourly', u'Daily', u'Weekly', u'Fortnightly', u'Monthly', u'Yearly'], 0)
				
				if Repeat!=None:
					ContactNames = []
					for C in Contacts:
						ContactNames.append(C[0])
					SelectedContacts = appuifw.multi_selection_list(ContactNames, style='checkmark', search_field=1)
	
					if len(SelectedContacts) > 0:
						SSMS = None
						
						if EditScheduledSMS:
							SSMS = EditScheduledSMS
						else:
							SSMS = SMS()
							
						SSMS.Contacts = []

						for i in SelectedContacts:
							if -1 == Contacts[i][1]:
								FirstTime = True
								while True:
									if True == FirstTime:
										MobileNumber = appuifw.query(u'Enter mobile number', 'text')
									else:
										MobileNumber = appuifw.query(u'Enter another mobile number', 'text')
									if None != MobileNumber:
										SSMS.Contacts.append((unicode(MobileNumber), MobileNumber))
									else:
										break
									FirstTime = False
							else:
								SSMS.Contacts.append(Contacts[i])
			
						if len(SSMS.Contacts) > 0:
							SSMS.Message = Message
							SSMS.Date = Date
							SSMS.Time = Time
							SSMS.Repeat = Repeat
			
						if EditScheduledSMS == None:
							ScheduledSMSList.append(SSMS)
				
						RefreshScheduledListBox()
			
						InitTimer()

	appuifw.app.title = u'SMSScheduler'

#+------------------------------------------------------+
#			set up menu items
#+------------------------------------------------------+	
	
def DoSetTab(Index):
	TabIndex = Index
	
	if Index == 0:
		appuifw.app.body = ScheduledListBox
		
		if len(ScheduledSMSList) > 0:
			appuifw.app.menu = [(u'Add', OnAddScheduledSMS), (u'Delete', OnDeleteScheduledSMS), (u'Edit', OnEditScheduledSMS), (u'Exit application', OnExit)]
		else:
			appuifw.app.menu = [(u'Add', OnAddScheduledSMS), (u'Exit application', OnExit)]			
	else:
		appuifw.app.body = HistoryListBox
		
		if len(HistorySMSList) > 0:
			appuifw.app.menu = [(u'Clear', OnClearHistorySMSs), (u'Exit application', OnExit)]
		else:
			appuifw.app.menu = [(u'Exit application', OnExit)]					

#+------------------------------------------------------+
#			Exiting help
#+------------------------------------------------------+

def ExitKeyHandler():
	appuifw.note(u'To switch the application to the background use the menu key, use the left soft-key menu to Exit.')

#+------------------------------------------------------+
#			Find out days in given month
#+------------------------------------------------------+	
	
def GetDaysInMonth(m, y):
	DaysInMonth = 31
	if 1 == m:
		if isleap(y):
			DaysInMonth = 29
		else:
			DaysInMonth = 28
	if (3 == m) or (5 == m) or (8 == m) or (10 == m):
		DaysInMonth = 30
		
	return DaysInMonth

#+------------------------------------------------------+
#			
#+------------------------------------------------------+

def GetScheduledSMSTime(x):
	CurrentTime = gmtime(time())
	
	CurrentYear = CurrentTime[0]
	CurrentMonth = CurrentTime[1]
	CurrentDay = CurrentTime[2]
	CurrentHour = CurrentTime[3]
	CurrentMinute = CurrentTime[4]
	CurrentSecond = CurrentTime[5]
	
	if 0 == CurrentTime[8]:
		CurrentHour = CurrentHour + 1
	if 1 == CurrentTime[8]:
		CurrentHour = CurrentHour + 2

	ScheduledSMSTime = gmtime(x.Date + x.Time)
	
	ScheduledSMSYear = ScheduledSMSTime[0]
	ScheduledSMSMonth = ScheduledSMSTime[1] 
	ScheduledSMSDay = ScheduledSMSTime[2]
	ScheduledSMSHour = ScheduledSMSTime[3]
	ScheduledSMSMinute = ScheduledSMSTime[4]
	ScheduledSMSSecond = ScheduledSMSTime[5]
	
	if x.Repeat != 0:
		if ((ScheduledSMSYear * 12 * 30 * 24 * 60 * 60) + (ScheduledSMSMonth * 30 * 24 * 60 * 60) + (ScheduledSMSDay * 24 * 60 * 60) + (ScheduledSMSHour * 60 * 60) + (ScheduledSMSMinute * 60) + ScheduledSMSSecond) < ((CurrentYear * 12 * 30 * 24 * 60 * 60) + (CurrentMonth * 30 * 24 * 60 * 60) + (CurrentDay * 24 * 60 * 60) + (CurrentHour * 60 * 60) + (CurrentMinute * 60) + CurrentSecond):	
			if 1 == x.Repeat:
				# Hourly
				ScheduledSMSYear = CurrentYear
				ScheduledSMSMonth = CurrentMonth
				ScheduledSMSDay = CurrentDay
				ScheduledSMSHour = CurrentHour
				if ((ScheduledSMSMinute * 60) + ScheduledSMSSecond) < ((CurrentMinute * 60) + CurrentSecond):
					ScheduledSMSHour = ScheduledSMSHour + 1
					
					if ScheduledSMSHour > 23:
						ScheduledSMSHour = 0
						ScheduledSMSDay = ScheduledSMSDay + 1
						
						DaysInMonth = GetDaysInMonth(ScheduledSMSMonth, ScheduledSMSYear)
						if ScheduledSMSDay > DaysInMonth:
							ScheduledSMSDay = 1
							ScheduledSMSMonth = ScheduledSMSMonth + 1
							
							if ScheduledSMSMonth > 12:
								ScheduledSMSMonth = 1
								ScheduledSMSYear = ScheduledSMSYear + 1
			if 2 == x.Repeat:
				# Daily
				ScheduledSMSYear = CurrentYear
				ScheduledSMSMonth = CurrentMonth
				ScheduledSMSDay = CurrentDay
				
				if ((ScheduledSMSHour * 60 * 60) + (ScheduledSMSMinute * 60) + ScheduledSMSSecond) < ((CurrentHour * 60 * 60) + (CurrentMinute * 60) + CurrentSecond):
					ScheduledSMSDay = ScheduledSMSDay + 1
					
					DaysInMonth = GetDaysInMonth(ScheduledSMSMonth, ScheduledSMSYear)
					if ScheduledSMSDay > DaysInMonth:
						ScheduledSMSDay = 1
						ScheduledSMSMonth = ScheduledSMSMonth + 1
						
						if ScheduledSMSMonth > 12:
							ScheduledSMSMonth = 1
							ScheduledSMSYear = ScheduledSMSYear + 1
			if (3 == x.Repeat) or (4 == x.Repeat):
				# Weekly/Fortnightly
				while ((ScheduledSMSYear * 12 * 30 * 24 * 60 * 60) + (ScheduledSMSMonth * 30 * 24 * 60 * 60) + (ScheduledSMSDay * 24 * 60 * 60) + (ScheduledSMSHour * 60 * 60) + (ScheduledSMSMinute * 60) + ScheduledSMSSecond) < ((CurrentYear * 12 * 30 * 24 * 60 * 60) + (CurrentMonth * 30 * 24 * 60 * 60) + (CurrentDay * 24 * 60 * 60) + (CurrentHour * 60 * 60) + (CurrentMinute * 60) + CurrentSecond):
					if 3 == x.Repeat:
						ScheduledSMSDay = ScheduledSMSDay + 7
					else:
						ScheduledSMSDay = ScheduledSMSDay + 14
						
					DaysInMonth = GetDaysInMonth(CurrentMonth, CurrentYear)
					
					if ScheduledSMSDay > DaysInMonth:
						ScheduledSMSDay = ScheduledSMSDay - DaysInMonth
						ScheduledSMSMonth = ScheduledSMSMonth + 1
						
						if ScheduledSMSMonth > 12:
							ScheduledSMSMonth = 1
							ScheduledSMSYear = ScheduledSMSYear + 1
			if 5 == x.Repeat:
				# Monthly
				ScheduledSMSYear = CurrentYear
				ShceduledSMSMonth = CurrentMonth
				
				if ((ScheduledSMSDay * 24 * 60 * 60) + (ScheduledSMSHour * 60 * 60) + (ScheduledSMSMinute * 60) + ScheduledSMSSecond) < ((CurrentDay * 24 * 60 * 60) + (CurrentHour * 60 * 60) + (CurrentMinute * 60) + CurrentSecond):
					ScheduledSMSMonth = ScheduledSMSMonth + 1
						
					if ScheduledSMSMonth > 12:
						ScheduledSMSMonth = 1
						ScheduledSMSYear = ScheduledSMSYear + 1			
			if 6 == x.Repeat:
				# Yearly
				ScheduledSMSYear = CurrentYear
				
				if ((ScheduledSMSMonth * 30 * 24 * 60 * 60) + (ScheduledSMSDay * 24 * 60 * 60) + (ScheduledSMSHour * 60 * 60) + (ScheduledSMSMinute * 60) + ScheduledSMSSecond) < ((CurrentMonth * 30 * 24 * 60 * 60) + (CurrentDay * 24 * 60 * 60) + (CurrentHour * 60 * 60) + (CurrentMinute * 60) + CurrentSecond):
					ScheduledSMSYear = ScheduledSMSYear + 1						
			
	return (ScheduledSMSYear * 365 * 24 * 60 * 60) + (ScheduledSMSMonth * 30 * 24 * 60 * 60) + (ScheduledSMSDay * 24 * 60 * 60) + (ScheduledSMSHour * 60 * 60) + (ScheduledSMSMinute * 60) + ScheduledSMSSecond	

#+------------------------------------------------------+
#			get current time
#+------------------------------------------------------+

def GetTime():
	CurrentTime = gmtime(time())
	
	CurrentYear = CurrentTime[0]
	CurrentMonth = CurrentTime[1]
	CurrentDay = CurrentTime[2]
	CurrentHour = CurrentTime[3]
	CurrentMinute = CurrentTime[4]
	CurrentSecond = CurrentTime[5]
	
	if 0 == CurrentTime[8]:
		CurrentHour = CurrentHour + 1
	if 1 == CurrentTime[8]:
		CurrentHour = CurrentHour + 2
		
	return (CurrentYear * 365 * 24 * 60 * 60) + (CurrentMonth * 30 * 24 * 60 * 60) + (CurrentDay * 24 * 60 * 60) + (CurrentHour * 60 * 60) + (CurrentMinute * 60) + CurrentSecond

	
#+------------------------------------------------------+
#		Initiate timer
#+------------------------------------------------------+

def InitTimer():
	Timer.cancel()

	Time = GetTime()
	
	NextScheduledSMSTime = -1
	NextScheduledSMSIndex = -1
	
	ScheduledSMSIndex = 0
	for x in ScheduledSMSList:
		ScheduledSMSTime = GetScheduledSMSTime(x)
		
		if ((-1 == NextScheduledSMSTime) or (ScheduledSMSTime < NextScheduledSMSTime)) and (ScheduledSMSTime > Time):
			NextScheduledSMSTime = ScheduledSMSTime
			NextScheduledSMSIndex = ScheduledSMSIndex
			
		ScheduledSMSIndex =  ScheduledSMSIndex + 1
			
	if NextScheduledSMSIndex != -1:
		Interval = NextScheduledSMSTime - Time
		IntervalSeconds = Interval % 60
		IntervalMinutes = ((Interval - IntervalSeconds) / 60) % 60
		IntervalHours = ((Interval - IntervalSeconds - (IntervalMinutes * 60)) / (60 * 60)) % 24
		IntervalDays = ((Interval - IntervalSeconds - (IntervalMinutes * 60) - (IntervalHours * 60 * 60)) / (24 * 60 * 60)) % 30
		IntervalMonths = ((Interval - IntervalSeconds - (IntervalMinutes * 60) - (IntervalHours * 60 * 60) - (IntervalDays * 24 * 60 * 60)) / (30 * 24 * 60 * 60)) % 12
		IntervalYears = int(((Interval - IntervalSeconds - (IntervalMinutes * 60) - (IntervalHours * 60 * 60) - (IntervalDays * 24 * 60 * 60)) / (30 * 24 * 60 * 60)) / 12)
		IntervalString = u'Time till next SMS is sent: '
		if IntervalYears < 10:
			IntervalString = IntervalString + u'0'
		IntervalString = IntervalString + unicode(IntervalYears) + u'/'		
		if IntervalMonths < 10:
			IntervalString = IntervalString + u'0'
		IntervalString = IntervalString + unicode(IntervalMonths) + u'/'
		if IntervalDays < 10:
			IntervalString = IntervalString + u'0'
		IntervalString = IntervalString + unicode(IntervalDays) + u' '
		if IntervalHours < 10:
			IntervalString = IntervalString + u'0'
		IntervalString = IntervalString + unicode(IntervalHours) + u':'
		if IntervalMinutes < 10:
			IntervalString = IntervalString + u'0'
		IntervalString = IntervalString + unicode(IntervalMinutes) + u':'
		if IntervalSeconds < 10:
			IntervalString = IntervalString + u'0'
		IntervalString = IntervalString + unicode(IntervalSeconds)
		appuifw.note(IntervalString)
		
		if Interval < 1000:
			ScheduledSMSIndex = 0
			for x in ScheduledSMSList:
				if ScheduledSMSIndex == NextScheduledSMSIndex:
					x.Send = True
				else:
					x.Send = False
				
				ScheduledSMSIndex = ScheduledSMSIndex + 1		
				
			Timer.after(Interval, OnTimer)
		else:
			for x in ScheduledSMSList:
				x.Send = False		
				
			Timer.after(1000, OnTimer)

#+------------------------------------------------------+
#			Schedule a new SMS
#+------------------------------------------------------+

def OnAddScheduledSMS():
	AddEditScheduledSMS(None)

#+------------------------------------------------------+
#		Clear History
#+------------------------------------------------------+

def OnClearHistorySMSs():
	while len(HistorySMSList) > 0:
		HistorySMSList.remove(HistorySMSList[0])
	
	RefreshHistoryListBox()

#+------------------------------------------------------+
#			Delete scheduled SMS
#+------------------------------------------------------+

def OnDeleteScheduledSMS():
	ScheduledSMSList.remove(ScheduledSMSList[ScheduledListBox.current()])
	
	RefreshScheduledListBox()
	
	InitTimer()

#+------------------------------------------------------+
#			Edit an scheduled SMS
#+------------------------------------------------------+	

def OnEditScheduledSMS():
	AddEditScheduledSMS(ScheduledSMSList[ScheduledListBox.current()])

	
#+------------------------------------------------------+
#			Exit
#+------------------------------------------------------+
def OnExit():
	AppLock.signal()

#+------------------------------------------------------+
#	Navigation through history
#+------------------------------------------------------+

def OnHistoryListBoxKeyDownArrow():
	if len(HistorySMSList) > 0:
		ListBoxIndex = HistoryListBox.current() + 1
			
		if ListBoxIndex >= len(HistorySMSList):
			ListBoxIndex = 0
	
		ShowToolTip(HistorySMSList[ListBoxIndex])	

def OnHistoryListBoxKeyUpArrow():
	if len(HistorySMSList) > 0:
		ListBoxIndex = HistoryListBox.current() - 1
			
		if ListBoxIndex < 0:
			ListBoxIndex = len(HistorySMSList) - 1
	
		ShowToolTip(HistorySMSList[ListBoxIndex])

#+------------------------------------------------------+
#			Cancellation
#+------------------------------------------------------+

def OnScheduledListBoxKeyBackspace():
	ScheduledSMSList.remove(ScheduledSMSList[ScheduledListBox.current()])
	
	RefreshScheduledListBox()
	
	InitTimer()

#+------------------------------------------------------+
#			Navigation through scheduled sms
#+------------------------------------------------------+

def OnScheduledListBoxKeyDownArrow():
	if len(ScheduledSMSList) > 0:
		ListBoxIndex = ScheduledListBox.current() + 1
			
		if ListBoxIndex >= len(ScheduledSMSList):
			ListBoxIndex = 0
	
		ShowToolTip(ScheduledSMSList[ListBoxIndex])	

def OnScheduledListBoxKeyUpArrow():
	if len(ScheduledSMSList) > 0:
		ListBoxIndex = ScheduledListBox.current() - 1
			
		if ListBoxIndex < 0:
			ListBoxIndex = len(ScheduledSMSList) - 1
	
		ShowToolTip(ScheduledSMSList[ListBoxIndex])

#+------------------------------------------------------+
#		Send SMS if it's time
#+------------------------------------------------------+
def OnTimer():
	for SSMS in ScheduledSMSList:
		if SSMS.Send == True:
			for C in SSMS.Contacts:
				messaging.sms_send(C[1], SSMS.Message)
			
			if SSMS.Repeat == 0:
				ScheduledSMSList.remove(SSMS)
				
				HistorySMSList.append(SSMS)

				RefreshScheduledListBox()
				
				RefreshHistoryListBox()
				
	InitTimer()

#+------------------------------------------------------+
#			Refresh history box after sent messages
#+------------------------------------------------------+

def RefreshHistoryListBox():
	Entries = []
	
	if len(HistorySMSList) > 0:
		for x in HistorySMSList:
			Text = u''
			
			Text = x.Contacts[0][0]
			
			if len(x.Contacts) > 1:
				Text = Text + u'...'
				
			Text = Text + u': '
			Text = Text + x.Message
			
			RepeatString = u''
			if 0 != x.Repeat:
				if 1 == x.Repeat:
					RepeatString = u' (Hourly)'
				if 2 == x.Repeat:
					RepeatString = u' (Daily)'					
				if 3 == x.Repeat:
					RepeatString = u' (Weekly)'					
				if 4 == x.Repeat:
					RepeatString = u' (Fortnightly)'					
				if 5 == x.Repeat:
					RepeatString = u' (Monthly)'					
				if 6 == x.Repeat:
					RepeatString = u' (Yearly)'					
				
			Entries.append((Text, unicode(format_time(x.Date + x.Time) + RepeatString)))
			
		HistoryListBox.set_list(Entries)
		
		appuifw.app.menu = [(u'Clear', OnClearHistorySMSs), (u'Exit application', OnExit)]
	else:
		HistoryListBox.set_list([(u'Empty', u'')])
		
		appuifw.app.menu = [(u'Exit application', OnExit)]

#+------------------------------------------------------+
#		Refresh scheduled SMS box
#+------------------------------------------------------+
def RefreshScheduledListBox():
	Entries = []
	
	if len(ScheduledSMSList) > 0:
		for x in ScheduledSMSList:
			Text = u''
			
			Text = x.Contacts[0][0]
			
			if len(x.Contacts) > 1:
				Text = Text + u'...'
				
			Text = Text + u': '
			Text = Text + x.Message
			
			RepeatString = u''
			if 0 != x.Repeat:
				if 1 == x.Repeat:
					RepeatString = u' (Hourly)'
				if 2 == x.Repeat:
					RepeatString = u' (Daily)'					
				if 3 == x.Repeat:
					RepeatString = u' (Weekly)'					
				if 4 == x.Repeat:
					RepeatString = u' (Fortnightly)'					
				if 5 == x.Repeat:
					RepeatString = u' (Monthly)'					
				if 6 == x.Repeat:
					RepeatString = u' (Yearly)'					
				
			Entries.append((Text, unicode(format_time(x.Date + x.Time) + RepeatString)))
			
		ScheduledListBox.set_list(Entries)

		if TabIndex == 0:
			appuifw.app.menu = [(u'Add', OnAddScheduledSMS), (u'Delete', OnDeleteScheduledSMS), (u'Edit', OnEditScheduledSMS), (u'Exit application', OnExit)]
	else:
		ScheduledListBox.set_list([(u'Empty', u'')])
		
		if TabIndex == 0:
			appuifw.app.menu = [(u'Add', OnAddScheduledSMS), (u'Exit application', OnExit)]	

#+------------------------------------------------------+
#	Edit/Add according to selection
#+------------------------------------------------------+

def ScheduledListBoxObserve():
	if len(ScheduledSMSList) > 0:
		AddEditScheduledSMS(ScheduledSMSList[ScheduledListBox.current()])
	else:
		AddEditScheduledSMS(None)

def ShowToolTip(SSMS):
#	Text = u'To: '
#	
#	ContactIndex = 0
#	for C in SSMS.Contacts:
#		Text = Text + C[0]
#		if ContactIndex < (len(SSMS.Contacts) - 1):
#			Text = Text + u', '
#		ContactIndex = ContactIndex + 1
#		
#	InfoPopup.show positioning not working in this version of PyS60				
#	ToolTip.show(Text, (0, 0), 5000, 0, appuifw.EHLeftVBottom)
	return

#+------------------------------------------------------+
#		Change tabs
#+------------------------------------------------------+
def TabSelChange(Index):
	DoSetTab(Index)

#+------------------------------------------------------+
# 		Default entries in boxes
#+------------------------------------------------------+
ScheduledListBox = appuifw.Listbox([(u'Empty', u'')], ScheduledListBoxObserve)	
HistoryListBox = appuifw.Listbox([(u'Empty', u'')])	

#+------------------------------------------------------+
#		Main 
#+------------------------------------------------------+
appuifw.app.title = u'SMSScheduler'

ContactsDB = contacts.open()

for i in ContactsDB.keys():
#	print i
	if ContactsDB[i].find('mobile_number')[0].value:
		ContactMobileNumber = ContactsDB[i].find('mobile_number')[0].value
#		print ContactMobileNumber
		if ContactMobileNumber and (len(ContactMobileNumber) > 0):
			ContactName = ContactsDB[i].find('first_name')[0].value
#			print ContactName
			if 0 == len(ContactName):
				Contacts.append((u'(unamed)', ContactMobileNumber))
			else:
				Contacts.append((ContactName, ContactMobileNumber))
			
Contacts.sort()
Contacts.insert(0, (u'*** New ***', -1))

try:
	f = open('e:\smsscheduler_session.cfg','rt')

	content = f.read()
	config = eval(content)
	f.close()

	if SessionConfigFileIDStr == config.get('FileIDStr', ''):
		Version = config.get('Version', '')

		if Version <= SessionConfigFileVersion:
			ScheduledSMSCount = config.get('ScheduledSMSCount', 0)

			ScheduledSMSIndex = 0
			while ScheduledSMSIndex < ScheduledSMSCount:
				SSMS = SMS()
				
				# Need to do this or subsequent instances of SMS use the same Conatcs instance as previous SMS instances
				# leading to all SMSs being sent to the same contacts!
				SSMS.Contacts = []

				SSMS.Message = config.get('ScheduledSMS' + unicode(ScheduledSMSIndex) + 'Message', '')
				SSMS.Date = config.get('ScheduledSMS' + unicode(ScheduledSMSIndex) + 'Date', '')
				SSMS.Time = config.get('ScheduledSMS' + unicode(ScheduledSMSIndex) + 'Time', '')
				SSMS.Repeat = config.get('ScheduledSMS' + unicode(ScheduledSMSIndex) + 'Repeat', '')
				
				ContactCount = config.get('ScheduledSMS' + unicode(ScheduledSMSIndex) + 'ContactCount', 0)
				
				ContactIndex = 0
				while ContactIndex < ContactCount:
					SSMS.Contacts.append(config.get('ScheduledSMS' + unicode(ScheduledSMSIndex) + 'Contact' + unicode(ContactIndex), ''))
					
					ContactIndex = ContactIndex + 1
					
				ScheduledSMSList.append(SSMS)
				
				ScheduledSMSIndex = ScheduledSMSIndex + 1
				
			ScheduledSMSCount = config.get('ScheduledSMSCount', 0)

			if Version >= 1.2:
				HistorySMSCount = config.get('HistorySMSCount', 0)
				
				HistorySMSIndex = 0
				while HistorySMSIndex < HistorySMSCount:
					SSMS = SMS()
					
					# Need to do this or subsequent instances of SMS use the same Conatcs instance as previous SMS instances
					# leading to all SMSs being sent to the same contacts!
					SSMS.Contacts = []

					SSMS.Message = config.get('HistorySMS' + unicode(HistorySMSIndex) + 'Message', '')
					SSMS.Date = config.get('HistorySMS' + unicode(HistorySMSIndex) + 'Date', '')
					SSMS.Time = config.get('HistorySMS' + unicode(HistorySMSIndex) + 'Time', '')
					SSMS.Repeat = config.get('HistorySMS' + unicode(HistorySMSIndex) + 'Repeat', '')
					
					ContactCount = config.get('HistorySMS' + unicode(HistorySMSIndex) + 'ContactCount', 0)
					
					ContactIndex = 0
					while ContactIndex < ContactCount:
						SSMS.Contacts.append(config.get('HistorySMS' + unicode(HistorySMSIndex) + 'Contact' + unicode(ContactIndex), ''))
						
						ContactIndex = ContactIndex + 1
						
					HistorySMSList.append(SSMS)
					
					HistorySMSIndex = HistorySMSIndex + 1				
		else:
			appuifw.note(u'Old or invalid session configuration file', 'error')
except:
	print(u'No session configuration file found')

appuifw.app.set_tabs([u'Active', u'History'], TabSelChange)
appuifw.app.screen='normal'
RefreshScheduledListBox()
RefreshHistoryListBox()

ScheduledListBox.bind(EKeyUpArrow, OnScheduledListBoxKeyUpArrow)
ScheduledListBox.bind(EKeyDownArrow, OnScheduledListBoxKeyDownArrow)
ScheduledListBox.bind(EKeyBackspace, OnScheduledListBoxKeyBackspace)

HistoryListBox.bind(EKeyUpArrow, OnHistoryListBoxKeyUpArrow)
HistoryListBox.bind(EKeyDownArrow, OnHistoryListBoxKeyDownArrow)

DoSetTab(0)

InitTimer()

appuifw.app.exit_key_handler = ExitKeyHandler

AppLock.wait()

Timer.cancel()

config = {}
config['FileIDStr'] = SessionConfigFileIDStr
config['Version'] = SessionConfigFileVersion
config['ScheduledSMSCount'] = len(ScheduledSMSList)
ScheduledSMSIndex = 0
for SSMS in ScheduledSMSList:
	config['ScheduledSMS' + unicode(ScheduledSMSIndex) + 'Message'] = SSMS.Message
	config['ScheduledSMS' + unicode(ScheduledSMSIndex) + 'Date'] = SSMS.Date
	config['ScheduledSMS' + unicode(ScheduledSMSIndex) + 'Time'] = SSMS.Time
	config['ScheduledSMS' + unicode(ScheduledSMSIndex) + 'Repeat'] = SSMS.Repeat
	ContactCount = len(SSMS.Contacts)
	config['ScheduledSMS' + unicode(ScheduledSMSIndex) + 'ContactCount'] = ContactCount
	ContactIndex = 0
	for C in SSMS.Contacts:
		config['ScheduledSMS' + unicode(ScheduledSMSIndex) + 'Contact' + unicode(ContactIndex)] = C
		ContactIndex = ContactIndex + 1
	ScheduledSMSIndex = ScheduledSMSIndex + 1
config['HistorySMSCount'] = len(HistorySMSList)
HistorySMSIndex = 0
for SSMS in HistorySMSList:
	config['HistorySMS' + unicode(HistorySMSIndex) + 'Message'] = SSMS.Message
	config['HistorySMS' + unicode(HistorySMSIndex) + 'Date'] = SSMS.Date
	config['HistorySMS' + unicode(HistorySMSIndex) + 'Time'] = SSMS.Time
	config['HistorySMS' + unicode(HistorySMSIndex) + 'Repeat'] = SSMS.Repeat
	ContactCount = len(SSMS.Contacts)
	config['HistorySMS' + unicode(HistorySMSIndex) + 'ContactCount'] = ContactCount
	ContactIndex = 0
	for C in SSMS.Contacts:
		config['HistorySMS' + unicode(HistorySMSIndex) + 'Contact' + unicode(ContactIndex)] = C
		ContactIndex = ContactIndex + 1
	HistorySMSIndex = HistorySMSIndex + 1	
f = open('e:\smsscheduler_session.cfg', 'wt')
f.write(repr(config))
f.close()

appuifw.app.set_exit()