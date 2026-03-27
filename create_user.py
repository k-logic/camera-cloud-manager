"""ユーザー作成スクリプト

Usage:
    # 管理者ユーザー（企業に属さない）
    python create_user.py --username admin --password secret --display-name "Admin" --admin

    # 企業ユーザー
    python create_user.py --username tanaka --password secret --display-name "Tanaka" --company "Example Corp"
"""
import argparse

from app.database import SessionLocal, engine, Base
from app.models.company import Company
from app.models.user import User
from app.services.auth_service import hash_password


def main():
    parser = argparse.ArgumentParser(description="Create user")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--company", help="Company name (created if not exists)")
    parser.add_argument("--admin", action="store_true", help="Create as admin user")
    args = parser.parse_args()

    if not args.admin and not args.company:
        parser.error("--company is required for non-admin users")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing = db.query(User).filter(User.username == args.username).first()
        if existing:
            print(f"User '{args.username}' already exists")
            return

        company_id = None
        if args.company:
            company = db.query(Company).filter(Company.name == args.company).first()
            if not company:
                company = Company(name=args.company)
                db.add(company)
                db.commit()
                db.refresh(company)
                print(f"Company created: {company.name} (id={company.id})")
            company_id = company.id

        user = User(
            company_id=company_id,
            username=args.username,
            hashed_password=hash_password(args.password),
            display_name=args.display_name,
            is_admin=args.admin,
        )
        db.add(user)
        db.commit()

        role = "admin" if args.admin else f"company={args.company}"
        print(f"User created: {args.username} ({role})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
