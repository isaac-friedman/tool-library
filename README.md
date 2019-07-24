# Tool Trackr  

Allows authenticated users to keep track of their tool collections using a  
library-like system. The catalog stores a variety of information about each  
tool and where it is located.

## Getting Started

### Prerequisites  
* Python 2.7
* Flask 1.1
* FlaskSQLAlchemy 2.x
* SQLAlchemy 0.8+


### Installing
1. Check that you have all prerequisites installed
2. Clone this repository
3. There is no database setup process! Every time the app is started, it  
checks if the database is present and creates it if not.

## Using  

### Running
1. Navigate to the directory where you installed the app.
2. Run `python app.py &` to start.
3. Enter `localhost:8000` in your browser address bar to access the app.

### JSON endpoints
Tool Trackr offers two JSON endpoints that allows logged-in users to view  
**but not edit** any tool in the system.
* /tools/json/ returns all information on all tools
* /tools/<tool id>/json/ returns all information on the given tool id

## Authors
* Isaac Friedman

## Acknowledgments
* Google Auth functions come straight from Google's documentation, slightly modified.
