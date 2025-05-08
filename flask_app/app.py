from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8000"}})  # Restrict to Django origin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ProductDescription model
class ProductDescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, unique=True, nullable=False)  # Matches Django Product.id
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url
        }

# ProductComment model
class ProductComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)  # Matches Django Product.id
    username = db.Column(db.String(100), nullable=False)  # Username of commenter
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'username': self.username,
            'comment': self.comment,
            'created_at': self.created_at.isoformat()
        }

# API endpoint to get product description by product_id
@app.route('/api/product/<int:product_id>', methods=['GET'])
def get_product_description(product_id):
    try:
        product = ProductDescription.query.filter_by(product_id=product_id).first()
        if product:
            logger.info(f"Product description retrieved for product_id={product_id}")
            return jsonify(product.to_dict()), 200
        logger.warning(f"Product not found for product_id={product_id}")
        return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        logger.error(f"Error retrieving product description for product_id={product_id}: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

# API endpoint to get comments for a product
@app.route('/api/product/<int:product_id>/comments', methods=['GET'])
def get_product_comments(product_id):
    try:
        comments = ProductComment.query.filter_by(product_id=product_id).order_by(ProductComment.created_at.desc()).all()
        logger.info(f"Retrieved {len(comments)} comments for product_id={product_id}")
        return jsonify([comment.to_dict() for comment in comments]), 200
    except Exception as e:
        logger.error(f"Error retrieving comments for product_id={product_id}: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

# API endpoint to submit a comment for a product
@app.route('/api/product/<int:product_id>/comments', methods=['POST'])
def submit_product_comment(product_id):
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('comment'):
            logger.warning(f"Invalid comment submission for product_id={product_id}: Missing username or comment")
            return jsonify({'error': 'Username and comment are required'}), 400
        comment = ProductComment(
            product_id=product_id,
            username=data['username'],
            comment=data['comment']
        )
        db.session.add(comment)
        db.session.commit()
        logger.info(f"Comment submitted for product_id={product_id} by {data['username']}")
        return jsonify(comment.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting comment for product_id={product_id}: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

# API endpoint to update a comment
@app.route('/api/product/comments/<int:comment_id>', methods=['PUT'])
def update_product_comment(comment_id):
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('comment'):
            logger.warning(f"Invalid comment update for comment_id={comment_id}: Missing username or comment")
            return jsonify({'error': 'Username and comment are required'}), 400
        comment = ProductComment.query.get(comment_id)
        if not comment:
            logger.warning(f"Comment not found for comment_id={comment_id}")
            return jsonify({'error': 'Comment not found'}), 404
        if comment.username != data['username']:
            logger.warning(f"Unauthorized update attempt for comment_id={comment_id} by {data['username']}")
            return jsonify({'error': 'Unauthorized: You can only update your own comments'}), 403
        comment.comment = data['comment']
        db.session.commit()
        logger.info(f"Comment updated for comment_id={comment_id} by {data['username']}")
        return jsonify(comment.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating comment for comment_id={comment_id}: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

# API endpoint to delete a comment
@app.route('/api/product/comments/<int:comment_id>', methods=['DELETE'])
def delete_product_comment(comment_id):
    try:
        data = request.get_json()
        if not data or not data.get('username'):
            logger.warning(f"Invalid comment deletion for comment_id={comment_id}: Missing username")
            return jsonify({'error': 'Username is required'}), 400
        comment = ProductComment.query.get(comment_id)
        if not comment:
            logger.warning(f"Comment not found for comment_id={comment_id}")
            return jsonify({'error': 'Comment not found'}), 404
        if comment.username != data['username']:
            logger.warning(f"Unauthorized deletion attempt for comment_id={comment_id} by {data['username']}")
            return jsonify({'error': 'Unauthorized: You can only delete your own comments'}), 403
        db.session.delete(comment)
        db.session.commit()
        logger.info(f"Comment deleted for comment_id={comment_id} by {data['username']}")
        return jsonify({'message': 'Comment deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting comment for comment_id={comment_id}: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

# Initialize database
with app.app_context():
    db.create_all()
    logger.info("Database tables created")

if __name__ == '__main__':
    app.run(debug=True)