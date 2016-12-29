gid=123456
nodes='0x0000 0x0702 0x0708 0x0306 0x0304 0x0d03 0x0d07 0x0401 0x0400'
gws='0x0205'

csv_path='docs/UID1470021754.csv'

echo "zigbee_report -gid $gid -n $nodes -gw $gws --csv_path $csv_path"
python3 inuithy/protocol/zigbee_report.py -gid $gid -n $nodes -gw $gws --csv_path $csv_path
if [ $? -eq 0 ] ;then echo "Zigbee report generation finished"; else echo "Zigbee report generation failed"; fi

