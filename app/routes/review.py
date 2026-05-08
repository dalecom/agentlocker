from flask import Blueprint, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models.review import Review, ReviewVote
from app.models.agent import Agent

review_bp = Blueprint('review', __name__)

@review_bp.route('/review/<int:review_id>', methods=['GET'])
@login_required
def get_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    return jsonify({
        'success': True,
        'review': {
            'content': review.content,
            'rating': review.rating
        }
    })

@review_bp.route('/review/<int:review_id>', methods=['PUT'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    if current_user.id != review.user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        review.rating = int(data['rating'])
        review.content = data['review_text']
        
        db.session.commit()
        review.agent.update_rating_stats()
        
        return jsonify({
            'success': True,
            'message': 'Review updated successfully'
        })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@review_bp.route('/review/<int:review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    try:
        review = Review.query.get_or_404(review_id)
        
        if review.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'You are not authorized to delete this review'
            }), 403
        
        agent = review.agent
        db.session.delete(review)
        db.session.commit()
        
        # Update agent rating statistics
        if agent:
            agent.update_rating_stats()
        
        return jsonify({
            'success': True,
            'message': 'Review deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting review: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error deleting review: {str(e)}'
        }), 500
    
@review_bp.route('/submit/<int:agent_id>', methods=['POST'])
@login_required
def submit(agent_id):
    print(f"Submit review request received for agent_id: {agent_id} by user_id: {current_user.id}")
    
    try:
        agent = Agent.query.get_or_404(agent_id)
        print(f"Agent found: {agent.name} (ID: {agent_id})")
        
        # Check if user already reviewed this agent
        existing_review = Review.query.filter_by(
            user_id=current_user.id,
            agent_id=agent_id
        ).first()
        
        if existing_review:
            print(f"User {current_user.id} has already reviewed agent {agent_id}")
            return jsonify({
                'success': False,
                'message': 'You have already reviewed this agent.'
            }), 400
        
        # Get data from JSON request
        data = request.get_json()
        print(f"Received data: {data}")
        
        # Create new review
        review = Review(
            user_id=current_user.id,
            agent_id=agent_id,
            rating=int(data['rating']),
            content=data['review_text'],
            title="Review"
        )
        
        db.session.add(review)
        db.session.commit()
        print(f"Review submitted successfully for agent_id: {agent_id} by user_id: {current_user.id}")
        
        # Update agent rating statistics
        agent.update_rating_stats()
        
        return jsonify({
            'success': True,
            'message': 'Review submitted successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting review for agent_id: {agent_id} by user_id: {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@review_bp.route('/review/<int:review_id>/vote', methods=['POST'])
@login_required
def vote(review_id):
    try:
        review = Review.query.get_or_404(review_id)
        data = request.get_json()
        vote_type = data.get('vote_type')
        
        if vote_type not in ['helpful', 'unhelpful']:
            return jsonify({
                'success': False,
                'message': 'Invalid vote type'
            }), 400
            
        # Check for existing vote
        existing_vote = ReviewVote.query.filter_by(
            user_id=current_user.id,
            review_id=review_id
        ).first()
        
        is_helpful = vote_type == 'helpful'
        
        if existing_vote:
            if existing_vote.is_helpful == is_helpful:
                # Remove vote if clicking same button
                db.session.delete(existing_vote)
                if is_helpful:
                    review.helpful_votes -= 1
                else:
                    review.unhelpful_votes -= 1
                user_vote = None
            else:
                # Change vote
                existing_vote.is_helpful = is_helpful
                if is_helpful:
                    review.helpful_votes += 1
                    review.unhelpful_votes -= 1
                else:
                    review.helpful_votes -= 1
                    review.unhelpful_votes += 1
                user_vote = vote_type
        else:
            # New vote
            vote = ReviewVote(
                user_id=current_user.id,
                review_id=review_id,
                is_helpful=is_helpful
            )
            db.session.add(vote)
            if is_helpful:
                review.helpful_votes += 1
            else:
                review.unhelpful_votes += 1
            user_vote = vote_type
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'helpful_votes': review.helpful_votes,
            'unhelpful_votes': review.unhelpful_votes,
            'user_vote': user_vote
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing vote: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your vote.'
        }), 500

