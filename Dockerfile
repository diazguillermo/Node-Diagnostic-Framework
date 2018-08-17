FROM python:3.6-jessie 

#ENV DISTRO_PATH ./distros/nginxnode/
#ENV GHOST_INSTALL /var/lib/ghost
#ENV GHOST_CONTENT /var/lib/ghost/content

RUN apt-get update -y
RUN apt-get install -y sudo python-pip \
    				 vim \
				iperf3
RUN sudo pip install bottle

#ADD $DISTRO_PATH/conf/supervisord.conf /etc/supervisord.conf

EXPOSE 8000
EXPOSE 2010

COPY sdf-rest.py /tmp/sdf-rest.py
COPY make_table.tpl /tmp/test/make_table.tpl
COPY tests.db /tmp/test/tests.db
#RUN chmod +x /usr/local/bin/image-entrypoint.sh

CMD [ "python", "/tmp/sdf-rest.py" ]
