#!/usr/bin/env bash
set -Eeuo pipefail

bundle exec rails runner -e production /opt/redmine-bootstrap.rb
exec bundle exec rails server -b 0.0.0.0 -p 3000 -e production
