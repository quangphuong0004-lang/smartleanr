from rest_framework import serializers
from .models import Quiz, QuizAnswer, QuizAttempt, Question, Choice


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Choice
        fields = ['id', 'text'] #không hiện is_correct khi học sinh làm bài
        

class ChoiceWithAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Choice
        fields = ['id', 'text', 'is_correct'] #Hiển thị sau khi đã nộp bài
        

#trả về câu hỏi và các đáp án
class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model  = Question
        fields = ['id', 'text', 'order', 'points', 'choices']
        
#Hiển thị kết quả, có cả đáp án đúng       
class QuestionWithAnswerSerializer(serializers.ModelSerializer):
    choices = ChoiceWithAnswerSerializer(many=True, read_only=True)

    class Meta:
        model  = Question
        fields = ['id', 'text', 'order', 'points', 'choices']
        
#Danh sách quiz, không trả về câu hỏi  
class QuizListSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(read_only=True)
    has_attempted = serializers.SerializerMethodField()
    my_score = serializers.SerializerMethodField()
    my_attempt_id = serializers.SerializerMethodField()


    class Meta:
        model  = Quiz
        fields = [
            'id', 'title', 'description', 'time_limit',
            'pass_score', 'is_published', 'question_count',
            'has_attempted', 'my_score', 'my_attempt_id', 'created_at',
        ]

    def get_has_attempted(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.attempts.filter(student=request.user, status='completed').exists()

    def get_my_score(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        attempt = obj.attempts.filter(student=request.user, status='completed').first()
        return round(attempt.score, 1) if attempt else None
    
    def get_my_attempt_id(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        attempt = obj.attempts.filter(
            student=request.user, status='completed'
        ).first()
        return str(attempt.id) if attempt else None

#bắt đầu làm bài, trả về câu hỏi và các câu trả lời, không có đáp án
class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Quiz
        fields = [
            'id', 'title', 'description', 'time_limit',
            'pass_score', 'question_count', 'questions',
        ]
        
#Tạo quiz
class QuizCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Quiz
        fields = ['title', 'description', 'time_limit', 'pass_score', 'is_published', 'course']
        

#Tạo câu hỏi
class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Question
        fields = ['text', 'order', 'points']
        

#Tạo đáp án đúng
class ChoiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Choice
        fields = ['text', 'is_correct']
        
#Kết quả sau khi nộp bài
class AttemptResultSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    is_passed = serializers.BooleanField(read_only=True)
    duration_seconds = serializers.IntegerField(read_only=True)

    class Meta:
        model  = QuizAttempt
        fields = ['id', 'score', 'is_passed', 'status', 'started_at', 'ended_at', 'duration_seconds', 'questions']

    #Trả về câu hỏi kèm đáp án đúng cùng với câu trả lời của học sinh
    def get_questions(self, attempt):
        answered = {a.question_id: a.choice_id for a in attempt.answers.all()}
        result   = []
        for q in attempt.quiz.questions.prefetch_related('choices').all():
            result.append({
                'id': str(q.id),
                'text': q.text,
                'points': q.points,
                'my_choice': str(answered.get(q.id)) if answered.get(q.id) else None,
                'choices': ChoiceWithAnswerSerializer(q.choices.all(), many=True).data,
            })
        return result