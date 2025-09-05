#!/usr/bin/env bash
# fio_matrix.sh - sweep read:write mixtures and dump CSV
# Usage: ./fio_matrix.sh /dev/nvme0n1 128k 32 60 > fio_matrix.csv
DEV=${1:-/dev/nvme0n1}
BS=${2:-128k}
QD=${3:-32}
RUNTIME=${4:-60}
echo "mix_read,MBps,IOPS,lat_mean_usec"
for MIX in 0 25 50 75 100; do
  fio --name=rw --filename=$DEV --rw=rw --rwmixread=$MIX --bs=$BS --iodepth=$QD --runtime=$RUNTIME --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > /tmp/fio.json
  MBPS=$(python - <<'PY'
import json,sys
j=json.load(open('/tmp/fio.json'))
# sum jobs
bw=sum(job['bw'] for job in j['jobs']) # KB/s
iops=sum(job['iops'] for job in j['jobs'])
lat=sum(job['clat']['mean'] for job in j['jobs'])/len(j['jobs']) if j['jobs'][0]['clat']['mean'] is not None else 0
print(f"{bw/1024:.1f},{iops:.0f},{lat:.1f}")
PY
)
  echo "$MIX,$MBPS"
done
