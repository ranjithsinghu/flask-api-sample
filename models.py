from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
db = SQLAlchemy()


class Metric(Base):
    __tablename__ = 'metric'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String, nullable=False, unique=True)
    description = db.Column(db.String, nullable=False)


class ValueDefinition(Base):
    __tablename__ = 'value_definition'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)

    metric_id = db.Column(db.Integer, db.ForeignKey('metric.id'),
                          nullable=False)
    metric = db.relationship('Metric',
                             backref=db.backref('value_definitions', lazy=True))

    def __repr__(self):
        return f"{self.metric.code} | Label: {self.label}, Type {self.type}"
