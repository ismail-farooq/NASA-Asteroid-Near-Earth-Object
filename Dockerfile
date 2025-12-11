# use official Python image
FROM python:3.11-slim

# set working directory
WORKDIR /flask_app

# copy the rest of the project
COPY . .

# install dependencies
RUN pip install -r requirements.txt

# expose port 5000
EXPOSE 5000

# change to the App directory and start Flask app
CMD ["python", "App/app.py"]