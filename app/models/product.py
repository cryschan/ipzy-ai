"""
Product SQLAlchemy 모델
Java 백엔드의 Product 엔티티와 동일한 구조
"""

from sqlalchemy import (ARRAY, TIMESTAMP, Boolean, Column, ForeignKey, Integer,
                        Index, String, Text)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Brand(Base):
    """브랜드 모델"""

    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    logo_url = Column(String(500))
    primary_style = Column(
        String(50)
    )  # hip_hop, minimalist, street, gorpcore, amekaji, cityboy
    brand_type = Column(String(20))  # CLOTHING, SHOES
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)

    # Relationship
    products = relationship("Product", back_populates="brand")


class Product(Base):
    """상품 모델"""

    __tablename__ = "products"

    __table_args__ = (
        Index(
            "ix_products_category_primary_style_is_active",
            "category",
            "primary_style",
            "is_active",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(
        String(20), nullable=False, index=True
    )  # TOP, BOTTOM, OUTER, SHOES, ACCESSORY
    sub_category = Column(String(50))
    primary_style = Column(String(50), index=True)  # 스타일 정보
    price = Column(Integer, nullable=False, index=True)
    original_price = Column(Integer)
    discount_percent = Column(Integer, default=0)
    image_url = Column(String(500), nullable=False)
    removed_background_image_url = Column(String(500))
    description = Column(Text)  # review 필드
    colors = Column(ARRAY(String))  # 색상 배열
    seasons = Column(ARRAY(String))  # 계절 배열
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    purchase_url = Column(String(500))
    deleted_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)

    # Relationship
    brand = relationship("Brand", back_populates="products")
