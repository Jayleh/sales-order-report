from unleashed import db
from unleashed.models import User

user = User.query.all()
print(user)