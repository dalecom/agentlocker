from app.extensions import db
from datetime import datetime

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Vote tracking columns
    helpful_votes = db.Column(db.Integer, default=0)
    unhelpful_votes = db.Column(db.Integer, default=0)
    helpfulness_score = db.Column(db.Integer, default=0)

    # Define relationships
    user = db.relationship('User')
    agent = db.relationship('Agent', back_populates='reviews')
    votes = db.relationship('ReviewVote', backref='review', lazy='dynamic', cascade='all, delete-orphan')

    def has_user_voted(self, user_id):
        """Check if a user has already voted on this review"""
        return ReviewVote.query.filter_by(
            review_id=self.id,
            user_id=user_id
        ).first() is not None

    def get_user_vote(self, user_id):
        """Get the user's vote on this review"""
        vote = ReviewVote.query.filter_by(
            review_id=self.id,
            user_id=user_id
        ).first()
        return vote.is_helpful if vote else None

    def increment_helpful(self):
        self.helpful_votes += 1
        self.update_helpfulness_score()

    def increment_unhelpful(self):
        self.unhelpful_votes += 1 
        self.update_helpfulness_score()

    def update_helpfulness_score(self):
        self.helpfulness_score = self.helpful_votes - self.unhelpful_votes
        db.session.commit()

class ReviewVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    is_helpful = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'review_id', name='uq_user_review_vote'),
    )