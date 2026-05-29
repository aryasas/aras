import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from .models import LandingSection
from api.core.lib.settings import settings
from api.core.lib.database import get_db

# gemini-flash
def seed_landing_sections(db: Session):
    sections_data = [
        {
            "key": "hero",
            "title": "Welcome to Aras Framework",
            "subtitle": "The ultimate solution for your business needs.",
            "body": "Aras provides a robust and flexible framework to build modern web applications with ease. Focus on your business logic, and let Aras handle the rest.",
            "image_url": "https://example.com/hero.jpg",
            "cta_label": "Get Started",
            "cta_url": "/signup",
            "sort_order": 10,
            "is_visible": True,
        },
        {
            "key": "feature.pos",
            "title": "Point of Sale Integration",
            "subtitle": "Streamline your retail operations.",
            "body": "Our framework seamlessly integrates with various Point of Sale systems, allowing for real-time inventory management and sales tracking.",
            "image_url": "https://example.com/feature-pos.jpg",
            "cta_label": "Learn More",
            "cta_url": "/features/pos",
            "sort_order": 20,
            "is_visible": True,
        },
        {
            "key": "feature.stock",
            "title": "Advanced Stock Management",
            "subtitle": "Optimize your supply chain.",
            "body": "Keep track of your inventory with advanced features like batch tracking, multiple warehouses, and automated reorder points.",
            "image_url": "https://example.com/feature-stock.jpg",
            "cta_label": "Explore Stock",
            "cta_url": "/features/stock",
            "sort_order": 30,
            "is_visible": True,
        },
        {
            "key": "feature.report",
            "title": "Insightful Reporting",
            "subtitle": "Make data-driven decisions.",
            "body": "Generate comprehensive reports on sales, inventory, customer behavior, and more, to gain valuable insights and drive growth.",
            "image_url": "https://example.com/feature-report.jpg",
            "cta_label": "View Reports",
            "cta_url": "/features/reports",
            "sort_order": 40,
            "is_visible": True,
        },
        {
            "key": "testimonial.one",
            "title": "A Game Changer!",
            "subtitle": "John Doe, CEO of ExampleCorp",
            "body": "Aras Framework transformed our business. The flexibility and power it offers are unmatched.",
            "image_url": "https://example.com/john-doe.jpg",
            "cta_label": None,
            "cta_url": None,
            "sort_order": 50,
            "is_visible": True,
        },
        {
            "key": "testimonial.two",
            "title": "Highly Recommended",
            "subtitle": "Jane Smith, Founder of StartupX",
            "body": "We built our entire platform on Aras, and it has been a fantastic experience. The development speed is incredible.",
            "image_url": "https://example.com/jane-smith.jpg",
            "cta_label": None,
            "cta_url": None,
            "sort_order": 60,
            "is_visible": True,
        },
        {
            "key": "cta",
            "title": "Ready to Transform Your Business?",
            "subtitle": "Join thousands of successful companies using Aras.",
            "body": "Start your journey with Aras Framework today and unlock new possibilities for your business.",
            "image_url": "https://example.com/cta-background.jpg",
            "cta_label": "Sign Up for Free",
            "cta_url": "/signup",
            "sort_order": 70,
            "is_visible": True,
        },
    ]

    for data in sections_data:
        section = db.query(LandingSection).filter_by(key=data["key"]).first()
        if section:
            # Update existing section
            for key, value in data.items():
                setattr(section, key, value)
        else:
            # Create new section
            section = LandingSection(**data)
            db.add(section)
        db.commit()
        db.refresh(section)
    print("Landing sections seeded successfully.")


if __name__ == "__main__":
    # This ensures that the script can be run directly
    # from the api/ folder or from the project root.
    # We need to explicitly set up the database connection here.
    
    # Use the DATABASE_URL from settings
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        print("Seeding landing sections...")
        seed_landing_sections(db)
        print("Done.")
    except Exception as e:
        print(f"Error seeding landing sections: {e}")
        db.rollback()
    finally:
        db.close()
