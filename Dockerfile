FROM jupyterhub/jupyterhub:0.9.2

ADD jhubauthenticators /app/jhubauthenticators
ADD setup.py /app/setup.py
ADD version.py /app/version.py
ADD requirements.txt /app/requirements.txt

WORKDIR /app
RUN pip install -r requirements.txt \
    && touch README.rst \
    && python setup.py install

# Make sure the jupyter_config is mounted upon run
CMD ["jupyterhub", "-f", "/etc/jupyterhub/jupyterhub_config.py"]