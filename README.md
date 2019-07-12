# Tool Library  

Allows authenticated users to keep track of their tool collections using a  
library-like system. The catalog stores a variety of information about each  
tool and where it is located.

## Prerequisites  
* Python 2.7,3.4+
* FlaskSQLAlchemy 2.x
* SQLAlchemy 0.8+ or 1.0.10+ w/ Python 3.7

## Installing
1. Check that you have all prerequisites installed
2. Open a python shell in the app directory
3. Run the following code to create your database:  
```
from db_setup import db
db.create_all()
```
