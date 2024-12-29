#!/bin/bash

i2clog="/home/pi/RolloPi/i2clog.json"
temp_file=$(mktemp /dev/shm/tempfile.XXXXXX)

# Get the last entry of a JSON array
i2c_last_entry=$(jq '.logs[-1].i2c' "$i2clog")

# Output the last entry
#echo "Last Entry:"
#echo "$i2c_last_entry"
#echo ""

# Run the i2c_detect command and store the result in a variable
i2c_result=$(i2cdetect -y 1)
#echo "$i2c_result"
#i2c_result=$(ls)
# we need to parse the result trou a json file to have the same format as in the logfile.
parsed_json=$(jq -n --arg i2c "$i2c_result" \
	  '{i2c: $i2c}')
echo "$parsed_json" > "$temp_file"
parsed=$(jq '.i2c' "$temp_file")
#echo "Result:"
#echo "$parsed"
#echo ""

if [[ "$parsed" != "$i2c_last_entry" ]];
then
	#echo "I2C changed!"
	# Get the current date in YYYY-MM-DD format
	current_date=$(date +%Y-%m-%d)
	# Get the current time in HH:MM:SS format
	current_time=$(date +%H:%M:%S)

	# New entry to add, including the timestamp
	new_entry=$(jq -n --arg date "$current_date" --arg time "$current_time" --arg i2c "$i2c_result" \
	  '{date: $date, time: $time, i2c: $i2c}')


	#echo "new entry: $new_entry"

	# Add the new entry to the JSON array
	jq --argjson new_entry "$new_entry" '.logs += [$new_entry]' "$i2clog" > temp.json && mv temp.json "$i2clog"
fi

