#!/usr/bin/env bash

gunicorn backend.wsgi:application