# -*- encoding: utf-8 -*-

from datetime import date
import json

try:
    from flaskext.babel import format_date
except ImportError:
    from flask.ext.babel import format_date
from sqlalchemy import CHAR, Column, Enum, func, Integer, String, Text, Unicode
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, deferred, relationship
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.sql.expression import and_, desc

from pokr.database import Base
from .bill_withdrawal import bill_withdrawal
from .candidacy import Candidacy
from .cosponsorship import cosponsorship
from .party import Party
from .party_affiliation import PartyAffiliation
from settings import THIS_ASSEMBLY


class Person(Base):
    __tablename__ = 'person'

    id = Column(Integer, primary_key=True)

    ### Fields ###
    name = Column(Unicode(20), nullable=False, index=True)
    name_en = Column(String(80), index=True)
    name_cn = Column(Unicode(20), index=True)

    gender = Column(Enum('m', 'f', name='enum_gender'), index=True)

    birthday = Column(CHAR(8), index=True)

    education = deferred(Column(ARRAY(Unicode(60))), group='profile')
    education_id = deferred(Column(ARRAY(String(20))), group='profile')

    address = deferred(Column(ARRAY(Unicode(20))), group='profile')
    address_id = deferred(Column(ARRAY(String(16))), group='profile')

    image = Column(String(1024))
    email = deferred(Column(Text), group='extra')
    twitter = deferred(Column(String(20)), group='extra')
    facebook = deferred(Column(String(80)), group='extra')
    blog = deferred(Column(String(255)), group='extra')
    homepage = deferred(Column(String(255)), group='extra')
    wiki = deferred(Column(Text), group='extra')
    extra_vars = deferred(Column(Text), group='extra')

    ### Relations ###
    candidacies = relationship('Candidacy',
            order_by='desc(Candidacy.assembly_id)',
            backref='person')
    bills_ = relationship('Bill',
            secondary=cosponsorship,
            order_by='desc(Bill.proposed_date)',
            backref='cosponsors')
    withdrawed_bills = relationship('Bill',
            secondary=bill_withdrawal,
            backref='withdrawers')
    parties = relationship('Party',
            secondary=PartyAffiliation.__table__,
            order_by='desc(PartyAffiliation.date)',
            backref=backref('members', lazy='dynamic'),
            lazy='dynamic')

    @hybrid_property
    def birthday_year(self):
        return int(self.birthday[:4])

    @birthday_year.expression
    def birthday_year(cls):
        return func.substr(cls.birthday, 1, 4)

    @property
    def birthday_month(self):
        return int(self.birthday[4:6]) or 1

    @property
    def birthday_day(self):
        return int(self.birthday[6:8]) or 1

    @property
    def birthday_date(self):
        return date(self.birthday_year,
                self.birthday_month,
                self.birthday_day)

    @property
    def birthday_formatted(self):
        return format_date(self.birthday_date)

    @property
    def age(self):
        return date.today().year+1-self.birthday_year

    @property
    def ages(self):
        if self.age < 30: return 30
        elif self.age >= 70: return 70
        else: return (self.age / 10) * 10

    @property
    def cur_party(self):
        return self.parties.first()

    @property
    def nelected(self):
        return len([c.assembly_id for c in self.candidacies if c.is_elected])

    @property
    def roles(self):
        # for badges
        r = []
        assembly_ids = [c.assembly_id for c in self.candidacies if c.is_elected]
        if THIS_ASSEMBLY in assembly_ids:
            r.append('official')
        if self.candidacies[0].district[0]==u'비례대표':
            r.append('proportional')
        return r
