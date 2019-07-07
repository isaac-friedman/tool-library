from db_setup import db, Category, User, Tool

cats = [
    Category(name='Hand Tools', description="Miscellaneous non-powered, one-person tools"),
    Category(name='Carpentry', description="Tools for building structures out of wood"),
    Category(name='Woodworking', description="Tools for making fine furniture, art pieces etc out of wood"),
    Category(name='Painting', description="Tools for covering surfaces with noxious liquids"),
    Category(name='Welding', description="Hot metal glue gun and accessories")
]

for cat in cats:
    db.session.add(cat)

db.session.commit()
