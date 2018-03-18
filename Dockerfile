FROM jupyterhub/jupyterhub:0.8.1

ADD jhub_remote_user_auth_mig_mount /app/jhub_remote_user_auth_mig_mount
ADD setup.py /app/setup.py
ADD version.py /app/version.py
ADD requirements.txt /app/requirements.txt

WORKDIR /app
RUN pip install -r requirements.txt \
    && touch README.rst \
    && python setup.py install

# Make sure the jupyter_config is mounted upon run
CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyter_config.py"]