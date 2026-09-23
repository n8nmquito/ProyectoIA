FROM redmine:6.1.4-bookworm

COPY bootstrap.rb /opt/redmine-bootstrap.rb
COPY start.sh /opt/redmine-start.sh
RUN sed -i 's/\r$//' /opt/redmine-start.sh

# El entrypoint oficial prepara database.yml y migra antes de este comando.
CMD ["bundle", "exec", "bash", "/opt/redmine-start.sh"]
