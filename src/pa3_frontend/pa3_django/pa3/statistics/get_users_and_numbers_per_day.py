#!/usr/bin/env python

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

import pickle
import datetime
from web.models import WaitingNumber

path = 'logs/'


def get_numbers_per_day(date_, global_set):
	tomorrow = int((date_ + datetime.timedelta(1)).strftime('%s'))
	today = int(date_.strftime('%s'))
	w_qs = global_set.filter(date__range=[today, tomorrow])
	c = w_qs.count()
	return c

def get_users_per_day(date_, tu=False):
	with open(os.path.join(path, str(date_))) as f:
		all_accesses = f.read().split('\n')
	accesses_filtered=[]
	for access in all_accesses:
		tsip = access.split(' ')
		if len(tsip) != 3:
			#not datetime, malformed
			continue
		ts = datetime.datetime.strptime(' '.join(tsip[:2]), '%Y-%m-%d %H:%M:%S.%f')
		# Tuesday => 13-16, not => 9-12 (opening times)
		if (date_.isoweekday() == 2 and ts.hour >= 13 and ts.hour <= 16) or \
		   (date_.isoweekday() != 2 and ts.hour >=  9 and ts.hour <= 12):
		   if not tu:
			   accesses_filtered.append(tsip[-1])
		   if tu and (tsip[-1].startswith('130.149.') or tsip[-1].startswith('141.23.')):
			   accesses_filtered.append(tsip[-1])

	return len(set(accesses_filtered))

current_date = datetime.date(2014,7,8)
end = datetime.date.today()

start = int(current_date.strftime('%s'))
end_ = int(end.strftime('%s'))
global_set = WaitingNumber.objects.filter(date__range=[start, end_])
global_set = global_set.filter(src__in=['H 02','H 10','H 19','H 23','H 25'])

f=open('data', 'w')
fTU=open('dataTU', 'w')
f.write('date, all, pap\n')
fTU.write('date, all, pap\n')
while current_date < end:
	if current_date.isoweekday() not in [3,6,7]:
		# PA is closed at Wednesday, Saturday, Sunday
		nums =  get_numbers_per_day(current_date, global_set)
		users = get_users_per_day(current_date)
		usersTU = get_users_per_day(current_date, tu=True)
		if nums and nums < 2000:
			# no numbers that day. Happens on friday, which are also closed during holidays
			# or just broken entries, >2000 => broken...

			users = users if users else 1
			usersTU = usersTU if usersTU else 1
			
			print '{0}, {1:4}, {2:4}, {3:4}'.format(current_date, nums, users, usersTU)
			f.write('{0}, {1:4}, {2:4}\n'.format(current_date, nums, users))
			fTU.write('{0}, {1:4}, {2:4}\n'.format(current_date, nums, usersTU))

	current_date += datetime.timedelta(1)
f.close()
fTU.close()
