#!/usr/bin/env sh

while true
do
	# look for sites at the end of July ...
	for i in 29 30 31
	do
		date=2018-07-${i}
		echo $date
		python campsites.py --start_date=$date
	done
	# ... and the beginning of August
	for i in $(seq 4)
	do
		date=2018-08-0${i}
		echo $date
		python campsites.py --start_date=$date
	done
	# print the date so I know when the last request was made
	date
	echo '********************************************************************************'
	# Wait a random interval between 0-3 minutes
	sleep $(($RANDOM % 180))
done
