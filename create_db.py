from models import Base, engine

print("Creating database tables...")
Base.metadata.create_all(engine)
print("Database tables created.")