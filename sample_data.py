from app import db, Category, User, Tool

super_user = User(firstname='Isaac', lastname='Friedman', email='isaac@isaac-friedman.com')

cats = [
    Category(name='Hand Tools', description="Miscellaneous non-powered, one-person tools"),
    Category(name='Carpentry', description="Tools for building structures out of wood"),
    Category(name='Woodworking', description="Tools for making fine furniture, art pieces etc out of wood"),
    Category(name='Painting', description="Tools for covering surfaces with noxious liquids"),
    Category(name='Welding', description="Hot metal glue gun and accessories")
]

tools = [
    Tool(name='Framing Hammer', description='18oz straight claw hammer',
        category_id=2, user_id=1),
    Tool(name='6-in-1 screwdriver',
        description='2 sizes each, philips and flat + nut drivers',
        location=2, category_id=1, user_id=1),
    Tool(name='Vise Grips',
        description="You don't need one until you wish you had one.",
        category_id=1, user_id=1)
]
"""
for cat in cats:
    db.session.add(cat)
"""
db.session.add(super_user)

for tool in tools:
    db.session.add(tool)

db.session.commit()
