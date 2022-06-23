from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_restx import Api, Resource, fields, reqparse

from models import *
import csv

from utils import get_or_create, object_as_dict

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db.init_app(app)
migrate = Migrate(app, db)
api = Api(title='Novisto API Documentation')
api.init_app(app)


@app.cli.command("upload_csv")
def upload_csv():
    with open('metrics.csv') as f:
        reader = csv.DictReader(f)
        for r in reader:
            metric, _created = get_or_create(
                db.session, Metric, defaults={
                    'description': r['metric_description']
                }, code=r['metric_code']
            )
            definition = ValueDefinition(
                label=r['value_label'],
                type=r['value_type'],
                metric=metric
            )
            db.session.add(definition)
            db.session.commit()
            print(f'{definition} added')


value_model = api.model('ValueDefinition', {
    'label': fields.String,
    'type': fields.String,
})

metric_model_post = api.model('Metric', {
    'code': fields.String(required=True),
    'description': fields.String(required=True),
})

metric_model = api.model('MetricDetail', {
    'id': fields.Integer,
    'code': fields.String(required=True),
    'description': fields.String(required=True),
    'value_definitions': fields.List(fields.Nested(value_model))
})


@api.route('/metrics')
class MetricListAPI(Resource):
    @api.marshal_with(metric_model, as_list=True)
    def get(self):
        """List all metrics"""
        all_metrics = db.session.query(Metric)
        return all_metrics.all(), 200

    @api.marshal_with(metric_model_post)
    @api.expect(metric_model_post, validate=True)
    def post(self):
        """Create new metrics"""
        context = api.payload
        code = context.get('code')
        description = context.get('description')

        metric, _created = get_or_create(
            db.session, Metric, defaults={
                'description': description
            }, code=code
        )
        if _created:
            return metric, 201
        api.abort(400, **{'errors': [
            {
                'field': 'code',
                'error_message': "code already exists"
            }
        ]})


@api.route('/metrics/<int:id>')
class MetricAPI(Resource):
    @api.marshal_with(metric_model)
    def get(self, id):
        """Get Metric details"""
        obj = db.session.query(Metric).filter(Metric.id == id).one_or_none()
        if not obj:
            api.abort(404)
        return obj

    @api.marshal_with(metric_model_post)
    @api.expect(metric_model_post, validate=True)
    def put(self, id):
        """Update metric"""
        context = api.payload
        code = context.get('code')
        obj = db.session.query(Metric).filter(Metric.id == id).one_or_none()
        if not obj:
            api.abort(404)
        elif db.session.query(Metric).filter(Metric.id != id, Metric.code == code).first():
            api.abort(400, **{'errors': [
                {
                    'field': 'code',
                    'error_message': "code already exists"
                }
            ]})

        description = context.get('description')

        obj.code = code
        obj.description = description
        db.session.commit()
        return obj, 200

    def delete(self, id):
        """Delete metric"""
        obj = db.session.query(Metric).filter(Metric.id == id).one_or_none()
        if not obj:
            api.abort(404)
        db.session.delete(obj)
        db.session.commit()


if __name__ == '__main__':
    app.run()
