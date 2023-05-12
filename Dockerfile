FROM ubuntu:latest
RUN apt-get update -y
RUN apt-get install python3-pip -y
WORKDIR /app
COPY SubErate /app
RUN pip install -r ./requirements.txt
EXPOSE 8501
CMD ["streamlit","run", "webapp.py"]




