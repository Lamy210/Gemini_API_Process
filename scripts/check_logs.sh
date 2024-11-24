#!/bin/bash

echo "Available log files:"
echo "1) All container logs"
echo "2) Processor logs"
echo "3) Watcher logs"
echo "4) Supervisor logs"

read -p "Select log file to view (1-4): " choice

case $choice in
    1)
        docker-compose logs -f
        ;;
    2)
        tail -f logs/processor.log
        ;;
    3)
        tail -f logs/watcher.log
        ;;
    4)
        tail -f logs/supervisord.log
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
