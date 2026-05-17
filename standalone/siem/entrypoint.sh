#!/usr/bin/env bash
set -euo pipefail

/usr/local/bin/sshd_setup.sh

service rsyslog start 2>/dev/null || true

# cti-collector 가 /opt/ccc 에 마운트되어 있다면 cron 등록.
if [ -f /opt/ccc/apps/cti-collector/collector.py ]; then
    cat > /etc/cron.d/ccc-cti <<'EOF'
# CCC CTI Collector — 매일 04:30 NVD CVE 수집
30 4 * * * root cd /opt/ccc && /usr/bin/python3 -m apps.cti-collector.collector --hours 24 --limit 30 >> /var/log/ccc-cti.log 2>&1
EOF
    chmod 644 /etc/cron.d/ccc-cti
    service cron start 2>/dev/null || true
    echo "[siem] cti-collector cron 등록 완료"
fi

echo "[siem] sshd foreground"
exec /usr/sbin/sshd -D -e
