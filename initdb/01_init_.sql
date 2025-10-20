-- runs automatically on first container start
CREATE USER vacaviz WITH PASSWORD 'vacaviz';
CREATE DATABASE vacaviz OWNER vacaviz;
GRANT ALL PRIVILEGES ON DATABASE vacaviz TO vacaviz;
