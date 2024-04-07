from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime, Boolean, ForeignKey, Float, Table, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, DeclarativeBase, Session

Base = declarative_base()

engine = create_engine('postgresql://user:pas123@postgres/auction')


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    phone = Column(String)
    username = Column(String)
    company_name = Column(String)
    company_website = Column(String)
    rating = Column(Float)
    status = Column(String)
    ban = Column(DateTime)
    nick = Column(String)

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
    price = Column(Integer)
    box_available = Column(Boolean)
    document_available = Column(Boolean)
    city = Column(String)
    comments = Column(String)
    owner_id = Column(BigInteger, ForeignKey('users.id'))

    owner = relationship("User", back_populates="items")
    photos = relationship("Photo", back_populates="item")


class Auction(Base):
    __tablename__ = 'auctions'
    id = Column(Integer, primary_key=True)
    bid_step = Column(Integer)
    start_date = Column(DateTime)
    duration = Column(DateTime)
    item_id = Column(Integer, ForeignKey('items.id'))
    owner_id = Column(BigInteger, ForeignKey('users.id'))
    winner_id = Column(BigInteger, ForeignKey('users.id'))
    state = Column(String)

    item = relationship("Item")
    owner = relationship("User", foreign_keys=[owner_id])
    winner = relationship("User", foreign_keys=[winner_id])


class Bid(Base):
    __tablename__ = 'bids'
    id = Column(Integer, primary_key=True)
    amount = Column(Integer)
    time = Column(DateTime)
    auction_id = Column(Integer, ForeignKey('auctions.id'))
    bidder_id = Column(BigInteger, ForeignKey('users.id'))

    auction = relationship("Auction")
    bidder = relationship("User", foreign_keys=[bidder_id])


class AutoBid(Base):
    __tablename__ = 'auto_bids'
    id = Column(Integer, primary_key=True)
    amount = Column(Integer)
    bid_time = Column(DateTime)
    auction_id = Column(Integer, ForeignKey('auctions.id'))
    bidder_id = Column(BigInteger, ForeignKey('users.id'))

    auction = relationship("Auction")
    bidder = relationship("User", foreign_keys=[bidder_id])


class Interest(Base):
    __tablename__ = 'interests'
    id = Column(Integer, primary_key=True)
    owner_id = Column(BigInteger, ForeignKey('users.id'))
    brand = Column(String)
    min_price = Column(Integer)
    max_price = Column(Integer)

    owner = relationship("User", back_populates="interests")


class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    reviewer_id = Column(BigInteger, ForeignKey('users.id'))
    owner_id = Column(BigInteger, ForeignKey('users.id'))
    note = Column(String)

    reviewer = relationship("User", foreign_keys=[reviewer_id])
    owner = relationship("User", foreign_keys=[owner_id])


class Buyer(Base):
    __tablename__ = 'buyers'
    id = Column(Integer, primary_key=True)
    auction_id = Column(Integer, ForeignKey('auctions.id'))
    buyer_id = Column(BigInteger, ForeignKey('users.id'))

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


def save_user(user):
    with connection.session as db:
        if db.get(User, user.id) is None:
            db.add(user)
            db.commit()


def get_user_info(user_id):
    with connection.session as db:
        return db.get(User, user_id)


def save_interest(interest):
    with connection.session as db:
        db.add(interest)
        db.commit()


def get_interests(user_id):
    with connection.session as db:
        interests = db.query(Interest).filter(Interest.owner_id == user_id)
        return interests


def delete_interest(interest_id):
    with connection.session as db:
        interest_to_delete = db.query(Interest).filter(Interest.id == interest_id).first()
        db.delete(interest_to_delete)  # удаляем объект
        db.commit()  # сохраняем изменения


def delete_user(user_id):
    with connection.session as db:
        user = db.query(User).filter(User.id == user_id).first()
        db.delete(user)
        db.commit()


def save_item(item):
    with connection.session as db:
        db.add(item)
        db.commit()
        return item.id


def get_item(item_id):
    with connection.session as db:
        return db.get(Item, item_id)


def get_items(user_id):
    with connection.session as db:
        items = db.query(Item).filter(Item.owner_id == user_id)
        return items


def get_auction_for_item(item_id):
    with connection.session as db:
        auction = db.query(Auction).filter(Auction.item_id == item_id).first()
        return auction


def delete_item(item_id):
    with connection.session as db:
        item = db.query(Item).filter(Item.id == item_id).first()
        photos = db.query(Photo).filter(Photo.item_id == item_id).all()
        for photo in photos:
            db.delete(photo)
            db.commit()
        db.delete(item)  # удаляем объект
        db.commit()


def get_all_users():
    with connection.session as db:
        return db.query(User).all()


def save_auction(auction):
    with connection.session as db:
        db.add(auction)
        db.commit()
        db.refresh(auction)
        return auction.id


def get_auction(auction_id):
    with connection.session as db:
        return db.get(Auction, auction_id)


def update_auction_state(auction_id, state):
    with connection.session as db:
        auction = db.get(Auction, auction_id)
        auction.state = state
        db.commit()


def get_interests_for_auction(auction_id):
    with connection.session as db:
        auction = db.get(Auction, auction_id)
        item_id = auction.item_id
        item = db.get(Item, item_id)
        brand = item.brand
        price = item.price
        return db.query(Interest).filter(Interest.brand == brand).filter(Interest.min_price <= price).filter(Interest.max_price >= price).all()


def get_coming_auctions(user_id):
    with connection.session as db:
        auctions_id = db.query(Buyer).filter(Buyer.buyer_id == user_id)
        auctions = []
        for au_id in auctions_id:
            auctions.append(get_auction(au_id.auction_id))
        coming_auctions = []
        if all(auctions):
            for au in auctions:
                if au.state == 'active' or au.state == 'going':
                    coming_auctions.append(au)
        return coming_auctions


def get_auctions_for_interest(interest):
    with connection.session as db:
        auction_ids = []
        auctions = db.query(Auction).filter(or_(Auction.state == 'active', Auction.state == 'going')).all()
        for auction in auctions:
            item = db.get(Item, auction.item_id)
            if item.id == interest.id and interest.min_price <= item.price <= interest.max_price:
                auction_ids.append(auction.id)
        return auction_ids


def save_buyer(auction_id, user_id):
    with connection.session as db:
        db.add(Buyer(auction_id=auction_id, buyer_id=user_id))
        db.commit()


def save_bid(bid, commit=True):
    with connection.session as db:
        db.add(bid)
        if commit:
            db.commit()
        else:
            db.flush()


def get_max_bid(auction_id):
    with connection.session as db:
        bids = db.query(Bid).filter(Bid.auction_id == auction_id).order_by(Bid.time).all()
        max_bid = bids[0]
        for b in bids:
            if b.amount > max_bid.amount:
                max_bid = b
        return max_bid


def save_photo(photo):
    with connection.session as db:
        db.add(photo)
        db.commit()


def get_photos_for_item(i_id):
    with connection.session as db:
        photos = db.query(Photo).filter(Photo.item_id == i_id).all()
        return photos


def get_auction_buyers(auction_id):
    with connection.session as db:
        buyers = db.query(Buyer).filter(Buyer.auction_id == auction_id)
        return buyers


def update_auction_time(auction_id, added_minutes):
    with connection.session as db:
        auction = db.get(Auction, auction_id)
        dt = auction.duration
        if dt.minute + added_minutes < 60:
            auction.duration = auction.duration.replace(minute=dt.minute + added_minutes)
        else:
            auction.duration = auction.duration.replace(hour=dt.hour + 1, minute=(dt.minute + added_minutes) % 60)
        db.commit()


def get_auction_to_participate(user_id):
    with connection.session as db:
        auctions = db.query(Auction).filter(or_(Auction.state == 'active', Auction.state == 'going')).all()
        user_auctions_list = db.query(Buyer).filter(Buyer.buyer_id == user_id).all()
        already_participate = []
        auctions_to_participate = []
        if all(user_auctions_list):
            for au in user_auctions_list:
                already_participate.append(au.auction_id)

            if all(auctions):
                for au in auctions:
                    if au.id not in already_participate:
                        auctions_to_participate.append(au.id)
        return auctions_to_participate


def update_winner_id(auction_id, user_id, commit=True):
    with connection.session as db:
        auction = db.get(Auction, auction_id)
        auction.winner_id = user_id
        if commit:
            db.commit()
        else:
            db.flush()


def save_auto_bid(auto_bid):
    with connection.session as db:
        db.add(auto_bid)
        db.commit()


def get_valid_auto_bids(auction_id):
    with connection.session as db:
        current_max_bid = get_max_bid(auction_id)
        auction = db.get(Auction, auction_id)
        auto_bids = db.query(AutoBid).filter(AutoBid.auction_id == auction_id).order_by(AutoBid.amount, AutoBid.bid_time.desc()).all()
        bid = 0
        previous_winner = 0
        if all(auto_bids):
            if len(auto_bids) == 1:
                if auto_bids[0].amount >= current_max_bid.amount + auction.bid_step:
                    if auto_bids[0].bidder_id != auction.winner_id:
                        new_bid = Bid(amount=current_max_bid.amount + auction.bid_step, time=auto_bids[0].bid_time, auction_id=auction_id, bidder_id=auto_bids[0].bidder_id)
                        db.add(new_bid)
                        previous_winner = auction.winner_id
                        b_id = auto_bids[0].bidder_id
                        auction.winner_id = b_id
                        bid = current_max_bid.amount + auction.bid_step
                        db.commit()
            elif len(auto_bids) > 1:
                if auto_bids[-1].amount >= current_max_bid.amount + auction.bid_step:
                    if auto_bids[-2].amount >= current_max_bid.amount + auction.bid_step:
                        if auto_bids[-1].amount > auto_bids[-2].amount:
                            if auto_bids[-1].bidder_id != auction.winner_id:
                                new_bid = Bid(amount=auto_bids[-2].amount + auction.bid_step, time=auto_bids[-1].bid_time, auction_id=auction_id, bidder_id=auto_bids[-1].bidder_id)
                                db.add(new_bid)
                                previous_winner = auction.winner_id
                                b_id = auto_bids[-1].bidder_id
                                auction.winner_id = b_id
                                bid = auto_bids[-2].amount + auction.bid_step
                                db.commit()
                            else:
                                new_bid = Bid(amount=current_max_bid + auction.bid_step, time=auto_bids[-2].bid_time,
                                              auction_id=auction_id, bidder_id=auto_bids[-2].bidder_id)
                                db.add(new_bid)
                                previous_winner = auction.winner_id
                                b_id = auto_bids[-2].bidder_id
                                auction.winner_id = b_id
                                bid = current_max_bid + auction.bid_step
                                db.commit()
                    else:
                        if auto_bids[-1].bidder_id != auction.winner_id:
                            new_bid = Bid(amount=current_max_bid.amount + auction.bid_step, time=auto_bids[-1].bid_time,
                                         auction_id=auction_id, bidder_id=auto_bids[-1].bidder_id)
                            db.add(new_bid)
                            previous_winner = auction.winner_id
                            b_id = auto_bids[-1].bidder_id
                            auction.winner_id = b_id
                            bid = current_max_bid.amount + auction.bid_step
                            db.commit()
        return bid, previous_winner


def get_auto_bidders(auction_id):
    with connection.session as db:
        bidders = db.query(AutoBid).filter(AutoBid.auction_id == auction_id).all()
        if all(bidders):
            bidders_ids = [b.id for b in bidders]
        return bidders_ids


def get_auto_bid(user_id, auction_id):
    with connection.session as db:
        auto_bid = db.query(AutoBid).filter(AutoBid.auction_id == auction_id).filter(AutoBid.bidder_id == user_id).first()
        return auto_bid


def get_auto_bid_by_id(auto_bid_id):
    with connection.session as db:
        auto_bid = db.get(AutoBid, auto_bid_id)
        return auto_bid


def change_auto_bid(auto_bid_id, amount):
    with connection.session as db:
        auto_bid = db.get(AutoBid, auto_bid_id)
        auto_bid.amount = amount
        db.commit()


def delete_auto_bid(auto_bid_id):
    with connection.session as db:
        auction_id = db.get(AutoBid, auto_bid_id)
        db.delete(auction_id)
        db.commit()


def get_all_not_finished_auctions():
    with connection.session as db:
        auctions = db.query(Auction).filter(or_(Auction.state == 'active', Auction.state == 'going')).all()
        return auctions


def is_item_on_auction(item_id):
    with connection.session as db:
        auction = db.query(Auction).filter(Auction.item_id == item_id).first()
        if auction is None:
            return False
        else:
            return True


def is_blocked(user_id):
    with connection.session as db:
        user = db.get(User, user_id)
        if user is not None:
            if user.ban is None:
                return False
            else:
                return True
        return False


def unblock_user(user_id):
    with connection.session as db:
        user = db.get(User,  user_id)
        user.ban = None
        db.commit()


def block_user(user_id, date):
    with connection.session as db:
        user = db.get(User, user_id)
        user.ban = date
        db.commit()


def get_biggest_auto_bid(auction_id):
    with connection.session as db:
        auto_bids = db.query(AutoBid).filter(AutoBid.auction_id == auction_id).order_by(AutoBid.amount).all()
        if all(auto_bids) and auto_bids:
            return auto_bids[-1].amount
        else:
            return 0


def delete_auction(auction_id):
    with connection.session as db:
        auction = get_auction(auction_id)
        db.delete(auction)
        db.commit()


def delete_bids_for_auction(auction_id):
    with connection.session as db:
        bids = db.query(Bid).filter(Bid.auction_id == auction_id).all()
        for bid in bids:
            db.delete(bid)
            db.commit()


def get_won_auctions(user_id):
    with connection.session as db:
        won_auctions = db.query(Auction).filter(Auction.winner_id == user_id)
        return won_auctions


def get_users_without_interests():
    with connection.session as db:
        users_without_interests_ids = []
        all_interests = db.query(Interest).all()
        users_with_interests_ids = []
        for interest in all_interests:
            users_with_interests_ids.append(interest.owner_id)
        users_with_interests_ids = set(users_with_interests_ids)
        all_users = db.query(User).all()
        for user in all_users:
            if user.id not in users_with_interests_ids:
                users_without_interests_ids.append(user.id)
        return users_without_interests_ids


