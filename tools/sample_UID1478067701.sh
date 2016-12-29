gid=123457
nodes='0x0000 0x0001 0x0102 0x0103 0x0206 0x0303 0x0304 0x0401 0x0400'
gws='0x0205'

csv_path='docs/UID1478067701.csv'

echo "zigbee_report -gid $gid -n $nodes -gw $gws --csv_path $csv_path"
python3 inuithy/protocol/zigbee_report.py -gid $gid -n $nodes -gw $gws --csv_path $csv_path
if [ $? -eq 0 ] ;then echo "Zigbee report generation finished"; else echo "Zigbee report generation failed"; fi

