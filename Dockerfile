FROM python:3.7


# remember to expose the port your app'll be exposed on.
EXPOSE 8080

RUN pip install -U pip

COPY /requirements.txt app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

# copy into a directory of its own (so it isn't in the toplevel dir)
COPY . /app

# run it!
# ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]

CMD streamlit run --server.port 8080 app.py
