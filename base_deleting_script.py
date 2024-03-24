from datetime import datetime
import os


from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Table, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, DeclarativeBase, Session

Base = declarative_base()

engine = create_engine('postgresql://user:pas123@postgres/auction')


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    phone = Column(String)
    username = Column(String)
    company_name = Column(String)
    company_website = Column(String)
    rating = Column(Float)
    status = Column(String)
    nick = Column(String)
    ban = Column(DateTime)

    items = relationship("Item", back_populates="owner")

    auction_buyer = relationship("Buyer", foreign_keys="[Buyer.buyer_id]")
    auctions_owned = relationship("Auction", foreign_keys="[Auction.owner_id]")
    auctions_won = relationship("Auction", foreign_keys="[Auction.winner_id]")
    bids = relationship("Bid", foreign_keys="[Bid.bidder_id]")
    auto_bids = relationship("AutoBid", foreign_keys="[AutoBid.bidder_id]")
    interests = relationship("Interest", back_populates="owner")
    reviews_written = relationship("Review", foreign_keys="[Review.reviewer_id]")
    reviews_received = relationship("Review", foreign_keys="[Review.owner_id]")


class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    brand = Column(String)
    reference = Column(String)
    price = Column(Float)
    box_available = Column(Boolean)
    document_available = Column(Boolean)
    comments = Column(String)
    owner_id = Column(Integer, ForeignKey('users.id'))

    owner = relationship("User", back_populates="items")
    photos = relationship("Photo", back_populates="item")


class Auction(Base):
    __tablename__ = 'auctions'
    id = Column(Integer, primary_key=True)
    bid_step = Column(Integer)
    start_date = Column(DateTime)
    duration = Column(DateTime)
    item_id = Column(Integer, ForeignKey('items.id'))
    owner_id = Column(Integer, ForeignKey('users.id'))
    winner_id = Column(Integer, ForeignKey('users.id'))
    state = Column(String)

    item = relationship("Item")
    owner = relationship("User", foreign_keys=[owner_id])
    winner = relationship("User", foreign_keys=[winner_id])


class Bid(Base):
    __tablename__ = 'bids'
    id = Column(Integer, primary_key=True)
    amount = Column(Float)
    time = Column(DateTime)
    auction_id = Column(Integer, ForeignKey('auctions.id'))
    bidder_id = Column(Integer, ForeignKey('users.id'))

    auction = relationship("Auction")
    bidder = relationship("User", foreign_keys=[bidder_id])


class AutoBid(Base):
    __tablename__ = 'auto_bids'
    id = Column(Integer, primary_key=True)
    amount = Column(Float)
    bid_time = Column(DateTime)
    auction_id = Column(Integer, ForeignKey('auctions.id'))
    bidder_id = Column(Integer, ForeignKey('users.id'))

    auction = relationship("Auction")
    bidder = relationship("User", foreign_keys=[bidder_id])


class Interest(Base):
    __tablename__ = 'interests'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    brand = Column(String)
    min_price = Column(Integer)
    max_price = Column(Integer)

    owner = relationship("User", back_populates="interests")


class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    reviewer_id = Column(Integer, ForeignKey('users.id'))
    owner_id = Column(Integer, ForeignKey('users.id'))
    note = Column(String)

    reviewer = relationship("User", foreign_keys=[reviewer_id])
    owner = relationship("User", foreign_keys=[owner_id])


class Buyer(Base):
    __tablename__ = 'buyers'
    id = Column(Integer, primary_key=True)
    auction_id = Column(Integer, ForeignKey('auctions.id'))
    buyer_id = Column(Integer, ForeignKey('users.id'))

    auction = relationship("Auction", foreign_keys=[auction_id])
    buyer = relationship("User", foreign_keys=[buyer_id])


class Photo(Base):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    item_id = Column(Integer, ForeignKey('items.id'))

    item = relationship("Item", back_populates="photos")


Base.metadata.create_all(bind=engine)


class DbConnection:
    def __init__(self):
        self.session = Session(autoflush=False, bind=engine)


connection = DbConnection()


Photo.__table__.drop(engine)
Buyer.__table__.drop(engine)
AutoBid.__table__.drop(engine)
Bid.__table__.drop(engine)
Auction.__table__.drop(engine)
Item.__table__.drop(engine)
Interest.__table__.drop(engine)
Review.__table__.drop(engine)
User.__table__.drop(engine)


def delete_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f'Ошибка при удалении файла {file_path}. {e}')


delete_files_in_folder('photos')









