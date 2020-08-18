#!/usr/bin/env bash

ps auxww | grep 'celery' | awk '{print $2}' | xargs kill -9

