"""初期データ投入スクリプト

adminユーザーとテスト用データを作成する。
既に存在するデータはスキップされる。

Usage:
    python seed.py
"""
from app.database import SessionLocal
from app.models.company import Company
from app.models.user import User
from app.services.auth_service import hash_password


SEED_DATA = {
    "companies": [
        {"name": "Example Corp"},
    ],
    "users": [
        {
            "username": "admin",
            "password": "admin",
            "display_name": "Admin",
            "is_admin": True,
            "company_name": None,
        },
        {
            "username": "tanaka",
            "password": "tanaka",
            "display_name": "Tanaka",
            "is_admin": False,
            "company_name": "Example Corp",
        },
    ],
}


def seed():
    db = SessionLocal()
    try:
        # Companies
        for data in SEED_DATA["companies"]:
            existing = db.query(Company).filter(Company.name == data["name"]).first()
            if existing:
                print(f"  Company '{data['name']}' already exists, skipping")
            else:
                db.add(Company(name=data["name"]))
                db.commit()
                print(f"  Company created: {data['name']}")

        # Users
        for data in SEED_DATA["users"]:
            company_id = None
            if data["company_name"]:
                company = db.query(Company).filter(Company.name == data["company_name"]).first()
                if company:
                    company_id = company.id

            existing = db.query(User).filter(User.username == data["username"]).first()
            if existing:
                if company_id and existing.company_id != company_id:
                    existing.company_id = company_id
                    db.commit()
                    print(f"  User '{data['username']}' updated: company_id={company_id}")
                else:
                    print(f"  User '{data['username']}' already exists, skipping")
                continue

            user = User(
                company_id=company_id,
                username=data["username"],
                hashed_password=hash_password(data["password"]),
                display_name=data["display_name"],
                is_admin=data["is_admin"],
            )
            db.add(user)
            db.commit()
            role = "admin" if data["is_admin"] else f"company={data['company_name']}"
            print(f"  User created: {data['username']} ({role})")
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding database...")
    seed()
    print("Done.")
